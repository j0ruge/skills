"""A porta privada só publica o conteúdo revisado, pelo gate da origem."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

from fixture_private import PASTA, SKILL, SLUG, PrivateWorld
import rw_auto as auto
import rw_gate as gate
import rw_store as store
from test_lean_window import MARK, T0, iso

REAL_STATUS = gate.Effects.status


class GateTest(unittest.TestCase):
    def setUp(self):
        w = self.w = PrivateWorld()
        self.addCleanup(w.cleanup)
        self.ctx = w.ctx()
        env = mock.patch.dict(os.environ, HOME=str(w.home), RW_FAKE_GATE_LOG=str(w.gate_log))
        env.start()
        self.addCleanup(env.stop)
        w.assert_fixture_origin(w.live)
        w.git(w.live, "config", "user.name", w.env["GIT_COMMITTER_NAME"])
        w.git(w.live, "config", "user.email", w.env["GIT_COMMITTER_EMAIL"])
        self.open_batch()
        self.effects = gate.Effects(self.ctx)
        status = mock.patch.object(gate.Effects, "status", create=True, return_value=(True, "ok"))
        self.status = status.start()
        self.addCleanup(status.stop)

    def open_batch(self):
        w = self.w
        self.base = self.remote_head()
        rid = self.rid = w.retro([{"repo": SLUG, "plugin": SKILL}], [{}])
        self.folder = auto.retro_dir(self.ctx, rid)
        pedido = auto.retro_pedido(self.ctx, rid)
        pedido["skills"] = [{"key": "lean:fixture", "plugin": SKILL, "label": SKILL, "skills": [SKILL],
                            "repo": SLUG, "modo": "auto-dry", "skill_path": f"{PASTA}/SKILL.md",
                            "origin_id": gate.rw.origin_id(gate.rw.origin_identity(str(w.remote)))}]
        auto._write_json(self.folder / "pedido.json", pedido)
        lot = store.prepare(self.ctx, rid, SKILL)
        self.wt = Path(lot["worktree"])
        self.lot = auto.lote_dir(self.ctx, rid, SKILL)
        self.assertEqual(w.git(self.wt, "remote", "get-url", "--push", "origin"), str(w.remote))

    def remote_head(self):
        return self.w.git(self.w.remote, "rev-parse", "refs/heads/main")

    def edit(self, *, changelog=True, path=None, text="Confira o resultado antes de seguir."):
        w = self.w
        if changelog:
            (self.wt / PASTA / "CHANGELOG.md").write_text("# Histórico\n\n## 2026-11-27\n\n- Nova lição.\n")
        with (self.wt / (path or f"{PASTA}/SKILL.md")).open("a") as fh:
            fh.write(f"\n{text}\n")
        w.git(self.wt, "add", "-A")
        env = dict(w.env, GIT_COMMITTER_DATE="2026-11-27T12:00:00Z", GIT_AUTHOR_DATE="2026-11-27T12:00:00Z")
        w.git(self.wt, "commit", "-qm", "Documenta uma prática", "-m", "Retrofit-Mode: autonomous", env=env)
        self.review()
        return w.git(self.wt, "rev-parse", "HEAD")

    def review(self, **fields):
        patch = store.seal(self.ctx, self.rid, SKILL, [1], [])["patch"]
        auto._write_json(self.lot / "diff.json", dict(
            {"patch": patch, "regra_repetida": None, "fora_das_licoes": None}, **fields))
        return patch

    def publish(self):
        return gate.publish(self.ctx, self.rid, SKILL, self.effects)

    def held(self, reason):
        out = self.publish()
        self.assertEqual((out["resultado"], out["motivo"], out.get("repo")), ("segurado", reason, SLUG), out)
        self.assertEqual(self.remote_head(), self.base)
        self.status.assert_not_called()
        return out["detalhe"]

    def logs(self):
        return [json.loads(line) for line in self.w.gate_log.read_text().splitlines()]

    def test_scope_keeps_the_requested_skill_when_main_adds_a_homonym(self):
        w = self.w
        self.edit()
        self.base = w.commit_on_origin({f"outra/{SKILL}/SKILL.md": "outra skill"}, "Acrescenta outra skill")
        self.assertEqual(self.publish()["motivo"], "auto-dry")

    def test_missing_gate(self):
        self.edit()
        hooks = self.w.tmp / "disabled-hooks"
        hooks.mkdir()
        hook = hooks / "pre-push"
        hook.write_text("#!/bin/sh\nexit 0\n")
        hook.chmod(0o644)
        self.w.git(self.wt, "config", "core.hooksPath", str(hooks))
        self.assertIn("sem pre-push", self.held("gate"))

    def test_gate_failure_keeps_bare(self):
        self.edit()
        with mock.patch.dict(os.environ, RW_FAKE_GATE_RC="2"):
            self.assertIn("gate: 2 passo(s)", self.held("gate"))

    def test_dry_then_approval_and_idempotent_retry(self):
        before = self.edit()
        self.assertIn("gate: 0 passo(s)", self.held("auto-dry"))
        self.assertEqual(self.logs()[0]["stdin"], f"HEAD {before} refs/heads/main {self.base}\n")
        approval = auto.approve(self.ctx, self.rid, SKILL)
        self.assertEqual(auto.load_aprovado(approval)["patch"], store.patch_id(self.wt, private=True))
        out = self.publish()
        sha = self.remote_head()
        self.assertEqual((out["resultado"], out["commit"], out.get("repo")), ("publicado", sha, SLUG), out)
        self.assertEqual(gate.exit_code(out), 0)
        self.assertEqual(sha, self.w.git(self.w.live, "rev-parse", "HEAD"))
        self.status.assert_called_once_with(SLUG, sha, mock.ANY, host="localhost")
        rehearsed, pushed = self.logs()[-2:]
        self.assertEqual(rehearsed, pushed)
        self.assertEqual(pushed["args"], ["origin", str(self.w.remote)])
        self.assertEqual(pushed["head"], sha)
        registry = auto.read_registry(self.ctx)
        self.assertEqual(self.publish(), out)
        self.assertEqual(auto.read_registry(self.ctx), registry)
        self.status.assert_called_once()

    def test_live_mode_pushes_unchanged_reviewed_sha(self):
        head = self.edit()
        with mock.patch.object(store, "lean_mode", return_value="auto"):
            out = self.publish()
        self.assertEqual((gate.exit_code(out), self.remote_head(), out["commit"]), (0, head, head), out)
        self.assertEqual(self.logs()[-2], self.logs()[-1])

    def test_changed_patch_invalidates_approval(self):
        self.edit()
        self.held("auto-dry")
        auto.approve(self.ctx, self.rid, SKILL)
        with (self.wt / PASTA / "SKILL.md").open("a") as fh:
            fh.write("\nUma emenda após a aprovação.\n")
        self.w.git(self.wt, "commit", "-qam", "Emenda a prática", "-m", "Retrofit-Mode: autonomous", "--amend",
                   env=dict(self.w.env, GIT_COMMITTER_DATE="2026-11-27T12:00:00Z"))
        self.held("revisao-desatualizada")
        self.review()
        self.held("auto-dry")

    def test_changelog_required(self):
        self.edit(changelog=False)
        self.held("sem-changelog")

    def test_private_patch_includes_store_list_paths(self):
        paths = ("scripts/public-names.txt", "scripts/private-names.sha256")
        self.w.commit_on_origin({
            "scripts/SKILL.md": (self.w.skill / "SKILL.md").read_text(),
            "scripts/CHANGELOG.md": "# Histórico\n",
            **dict.fromkeys(paths, "Conteúdo inicial da fixture.\n"),
        }, "Semeia uma skill em scripts")
        with (mock.patch.multiple(sys.modules[__name__], SKILL="scripts", PASTA="scripts"),
              mock.patch.object(self.effects, "push_private", side_effect=AssertionError("a prova não publica"))):
            self.open_batch()
            self.edit(path=paths[0])
            for path in paths:
                self.held("auto-dry")
                auto.approve(self.ctx, self.rid, SKILL)
                with (self.wt / path).open("a", encoding="utf-8") as fh:
                    fh.write("Nova linha da fixture.\n")
                self.w.git(self.wt, "commit", "-qa", "--amend", "--no-edit")
                refusal = gate.refuse(self.ctx, self.rid, SKILL, [])
                self.assertEqual(refusal and refusal[0], "revisao-desatualizada", (path, refusal))
                self.assertEqual(self.remote_head(), self.base)
                self.review()

    def test_out_of_scope(self):
        self.edit(path="scripts/gate_stub.py", text="# fora da pasta")
        self.held("escopo")

    def test_private_scan_reports_when_the_store_scanner_rejects_its_interface(self):
        with mock.patch.object(store, "_gate", return_value=(2, "interface da fixture")):
            with self.assertRaisesRegex(store.StoreError, "interface da fixture.*origin/main local da loja"):
                store.layer1(self.ctx, self.rid, self.wt, self.w.store,
                             private=True, base=self.base, head=self.base)

    def test_secret_is_not_overridable(self):
        self.edit(text="gh" + "p_" + "Z" * 36)
        self.held("segredo")
        auto.approve(self.ctx, self.rid, SKILL)
        self.held("segredo")

    def test_user_path_is_overridable(self):
        self.edit(path=f"{PASTA}/CHANGELOG.md",
                  text="Caminho: " + "/".join(("", "home", "fixture-user", "estado")))
        self.held("caminho")
        auto.approve(self.ctx, self.rid, SKILL)
        self.held("auto-dry")
        auto.approve(self.ctx, self.rid, SKILL)
        self.assertEqual(gate.exit_code(self.publish()), 0)

    def test_second_review_is_required_and_applies(self):
        self.edit()
        (self.lot / "diff.json").unlink()
        self.held("revisao-desatualizada")
        self.review(regra_repetida="a regra já consta na skill")
        self.held("regra-repetida")
        self.review(fora_das_licoes="mudança além do pedido")
        self.held("diff-alem-das-licoes")

    def test_second_review_is_read_once_for_both_findings(self):
        self.edit()
        with mock.patch.object(auto, "load_diff", wraps=auto.load_diff) as load:
            self.held("auto-dry")
        load.assert_called_once_with(self.lot / "diff.json")

    def test_private_evidence_uses_the_rebased_commit_pair(self):
        self.edit()
        self.w.commit_on_origin({"nota.md": "Avanço independente.\n"}, "Acrescenta uma nota")
        self.base = self.remote_head()
        with (mock.patch.object(store, "layer1", wraps=store.layer1) as scan,
              mock.patch.object(store, "patch_id", wraps=store.patch_id) as patch):
            self.held("auto-dry")
        head = self.w.git(self.wt, "rev-parse", "HEAD")
        self.assertEqual(self.w.git(self.wt, "rev-parse", "HEAD^"), self.base)
        options = dict(base=self.base, head=head, private=True)
        scan.assert_called_once_with(self.ctx, self.rid, self.wt, mock.ANY, **options)
        self.assertTrue(patch.call_args_list)
        self.assertTrue(all(call == mock.call(self.wt, **options) for call in patch.call_args_list))

    def test_private_seal_uses_the_same_commit_pair_for_identity_and_scan(self):
        head = self.edit()
        with (mock.patch.object(store, "layer1", wraps=store.layer1) as scan,
              mock.patch.object(store, "patch_id", wraps=store.patch_id) as patch):
            sealed = store.seal(self.ctx, self.rid, SKILL, [1], [])
        options = dict(base=self.base, head=head, private=True)
        self.assertEqual(sealed["commit"], head)
        scan.assert_called_once_with(self.ctx, self.rid, self.wt, mock.ANY, **options)
        patch.assert_called_once_with(self.wt, **options)

    def test_private_patch_identity_binds_the_edit_location(self):
        relative = f"{PASTA}/notas.md"
        original = "Confira.\nPrimeira seção.\nConfira.\nSegunda seção.\n"
        self.w.commit_on_origin({relative: original}, "Adiciona notas em duas seções")
        self.open_batch()
        self.edit()
        note = self.wt / relative
        note.write_text(original.replace("Confira.", "Valide.", 1))
        self.w.git(self.wt, "commit", "-qa", "--amend", "--no-edit")
        first = store.patch_id(self.wt, private=True)
        legacy = store.patch_id(self.wt)
        note.write_text("Confira.\nPrimeira seção.\nValide.\nSegunda seção.\n")
        self.w.git(self.wt, "commit", "-qa", "--amend", "--no-edit")
        self.assertEqual(store.patch_id(self.wt), legacy)
        self.assertNotEqual(store.patch_id(self.wt, private=True), first)

    def test_status_failure_keeps_published_sha(self):
        head = self.edit()
        self.status.return_value = False, "sem acesso"
        with mock.patch.object(store, "lean_mode", return_value="auto"):
            out = self.publish()
        self.assertEqual((gate.exit_code(out), out["instalacao"], self.remote_head(), out["commit"]),
                         (4, "status-falhou", head, head), out)
        self.assertEqual(self.w.git(self.w.live, "rev-parse", "HEAD"), head)
        self.assertIn("local/ci", gate.phrase(out))
        self.assertNotIn("instalada", gate.phrase(out))

    def test_status_uses_the_real_hook_summary_on_retry(self):
        head = self.edit()
        hookpath = self.w.tmp / "status-summary-hooks"
        hookpath.mkdir()
        hook = hookpath / "pre-push"
        hook.write_text('#!/bin/sh\necho "Verificação iniciada."\nprintf "%s\\n" "${RW_SUMMARY:-Ensaio passou.}"\n',
                        encoding="utf-8")
        hook.chmod(0o755)
        self.w.git(self.wt, "config", "core.hooksPath", str(hookpath))
        self.status.side_effect = [(False, "indisponível"), (True, "ok")]
        push = self.effects.push_private
        run = store.run

        def inspect_wrapper(command, **kwargs):
            if "push" in command:
                hooks = next(arg.removeprefix("core.hooksPath=") for arg in command
                             if isinstance(arg, str) and arg.startswith("core.hooksPath="))
                wrapper = (Path(hooks) / "pre-push").read_text(encoding="utf-8")
                self.assertIn('"$RW_GATE_PYTHON" -I -c', wrapper)
            return run(command, **kwargs)

        def real_summary(p, contract):
            with mock.patch.dict(os.environ, RW_SUMMARY="Publicação verificada."):
                return push(p, contract)

        with mock.patch.object(store, "lean_mode", return_value="auto"), \
                mock.patch.object(store, "run", side_effect=inspect_wrapper), \
                mock.patch.object(self.effects, "push_private", side_effect=real_summary):
            out = self.publish()
        self.assertEqual((out["instalacao"], out["commit"]), ("status-falhou", head), out)
        self.assertIn("Ensaio passou.", out["gate"])
        self.assertEqual(out.get("gate_push"), "Publicação verificada.")
        self.assertEqual(gate.exit_code(self.publish()), 0)
        self.assertEqual(self.status.call_args_list, [
            mock.call(SLUG, head, "Publicação verificada.", host="localhost"),
            mock.call(SLUG, head, "Publicação verificada.", host="localhost"),
        ])

    def test_push_requires_the_rehearsed_hook_content(self):
        self.edit()
        p = gate._Porta(self.ctx, self.rid, SKILL, [])
        with mock.patch.object(store, "lean_mode", return_value="auto"):
            refusal, contract = gate._check_private(p)
        self.assertIsNone(refusal)
        hook = self.wt / ".githooks/pre-push"
        hook.write_bytes(hook.read_bytes() + b"\n# Atualiza o comentario da fixture.\n")
        with mock.patch.object(store, "run", return_value=(0, "")) as run, \
                mock.patch.object(gate, "_private_origin", return_value=(str(self.w.remote), p.env, None)), \
                mock.patch.object(gate, "_prepush_path", return_value=hook):
            ok, detail = self.effects.push_private(p, contract)
        self.assertFalse(ok, detail)
        run.assert_not_called()

    def test_advance_failure_keeps_publication_and_retry_advances(self):
        head = self.edit()
        dirty = self.w.live / "novo"
        dirty.touch()
        with mock.patch.object(store, "lean_mode", return_value="auto"):
            out = self.publish()
        self.assertEqual((gate.exit_code(out), out["instalacao"], self.remote_head(), out["commit"]),
                         (4, "clone-atras", head, head), out)
        dirty.unlink()
        retry = self.publish()
        self.assertEqual((gate.exit_code(retry), self.w.git(self.w.live, "rev-parse", "HEAD")), (0, head), retry)
        self.status.assert_called_once()
        self.assertEqual(len(self.logs()), 2)

    def test_git_resolves_absolute_and_default_hook_paths(self):
        self.edit()
        w = self.w
        hook = self.wt / ".githooks/pre-push"
        default = w.live / ".git/hooks/pre-push"
        default.write_bytes(hook.read_bytes())
        default.chmod(0o755)
        for loc in (w.tmp / "hooks absolutos", None):
            if loc:
                loc.mkdir()
                target = loc / "pre-push"
                target.write_bytes(hook.read_bytes())
                target.chmod(0o755)
                w.git(self.wt, "config", "core.hooksPath", str(loc))
            else:
                w.git(self.wt, "config", "--unset", "core.hooksPath")
            self.held("auto-dry")
        self.assertEqual(len(self.logs()), 2)

    def test_distinct_repo_paths_have_distinct_origin_ids(self):
        rw = gate.rw

        def identity(url):
            origin = rw.origin_identity(url)
            self.assertIsNotNone(origin)
            self.assertEqual(origin[0], SLUG)
            return rw.origin_id(origin)

        base = "https://localhost"
        expected = identity(f"{base}/{SLUG}.git")
        for path in ("fixture/KB-libs.git", "Fixture/kb-libs.git", SLUG, f"{SLUG}.git/"):
            with self.subTest(path=path):
                self.assertNotEqual(identity(f"{base}/{path}"), expected)
        self.assertNotEqual(identity(f"localhost:{SLUG}.git/"), expected)
        self.assertNotEqual(identity(f"https://github.com:8443/{SLUG}.git"),
                            identity("https://github.com:8443/Fixture/KB-libs.git"))
        self.assertEqual(rw.origin_identity(f"https://github.com/{SLUG}"), [SLUG, "github.com", None])
        self.assertEqual(identity("https://GITHUB.com/Fixture/KB-libs.git/"),
                         identity(f"https://github.com/{SLUG}"))

    def test_origin_mismatch_holds_without_gate(self):
        self.edit()
        self.w.git(self.wt, "remote", "set-url", "--push", "origin", str(self.w.origin))
        self.held("escopo")
        self.assertFalse(self.w.gate_log.exists())

    def test_same_slug_effective_origin_mismatch_holds_before_fetch(self):
        self.edit()
        w = self.w
        url = f"https://other.example/{SLUG}.git"
        w.git(self.wt, "config", f"url.{url}.insteadOf", str(w.remote))
        self.assertEqual(w.git(self.wt, "remote", "get-url", "origin"), url)
        self.assertEqual(w.git(self.wt, "remote", "get-url", "--push", "origin"), url)
        with mock.patch.object(store, "_live_fetch", side_effect=AssertionError("fetch indevido")) as fetch:
            self.held("escopo")
        fetch.assert_not_called()
        self.assertFalse(w.gate_log.exists())

    def test_same_slug_replacement_of_configured_origin_holds_before_fetch(self):
        self.edit()
        w = self.w
        w.git(self.wt, "remote", "set-url", "origin", f"https://other.example/{SLUG}.git")
        with mock.patch.object(store, "_live_fetch", side_effect=AssertionError("fetch indevido")) as fetch:
            self.held("escopo")
        fetch.assert_not_called()
        self.assertFalse(w.gate_log.exists())

    def test_changed_transport_target_holds_before_fetch(self):
        self.edit()
        w = self.w
        authorized = f"git@localhost:{SLUG}.git"
        changed = f"ssh://git@localhost/{SLUG}.git"
        w.git(self.wt, "remote", "set-url", "origin", authorized)
        lot = json.loads((self.lot / "retrofit.json").read_text())
        lot["origin_id"] = gate.rw.origin_id(gate.rw.origin_identity(authorized))
        auto._write_json(self.lot / "retrofit.json", lot)
        p = gate._Porta(self.ctx, self.rid, SKILL, [])
        self.assertEqual(gate._private_origin(p)[0], authorized)

        w.git(self.wt, "config", f"url.{changed}.insteadOf", authorized)
        self.assertEqual(w.git(self.wt, "remote", "get-url", "origin"), changed)
        self.assertEqual(w.git(self.wt, "remote", "get-url", "--push", "origin"), changed)
        with mock.patch.object(store, "_live_fetch", side_effect=AssertionError("fetch indevido")) as fetch:
            self.held("escopo")
        fetch.assert_not_called()
        self.assertFalse(w.gate_log.exists())

    def test_fetch_rechecks_the_pinned_origin(self):
        w = self.w
        p = gate._Porta(self.ctx, self.rid, SKILL, [])
        origin = gate._private_origin(p)
        w.git(self.wt, "remote", "set-url", "origin", f"https://other.example/{SLUG}.git")
        run = store.run

        def no_fetch(command, **kw):
            self.assertNotIn("fetch", command)
            return run(command, **kw)

        with mock.patch.object(gate, "_private_origin", return_value=origin), \
                mock.patch.object(store, "run", side_effect=no_fetch):
            self.assertEqual(gate._private_fetch(p)[0], "fetch")

    def test_status_selects_the_host_even_with_another_gh_default(self):
        with mock.patch.dict(os.environ, GH_HOST="other.example"), \
                mock.patch.object(store, "run", return_value=(0, "")) as run:
            self.assertEqual(REAL_STATUS(self.effects, SLUG, self.base, "gate verde",
                                         host="forge.example"), (True, "local/ci"))
        self.assertEqual(run.call_args.args[0][:7],
                         ["gh", "api", "-X", "POST", f"repos/{SLUG}/statuses/{self.base}",
                          "--hostname", "forge.example"])

    def test_private_status_uses_api_host_not_ssh_port(self):
        self.assert_private_status_target("SSH://git@localhost:2222", "localhost")

    def test_private_status_custom_https_port_uses_valid_cli_arguments(self):
        self.assert_private_status_target("https://localhost:8443", "localhost",
                                          endpoint_prefix="https://localhost:8443/api/v3/")

    def assert_private_status_target(self, transport, api_host, *, endpoint_prefix=""):
        head = self.edit()
        url = f"{transport}/{SLUG}.git"
        expected = ["gh", "api", "-X", "POST", f"{endpoint_prefix}repos/{SLUG}/statuses/{head}",
                    "--hostname", api_host]
        private_origin = gate._private_origin
        run = store.run
        gh_calls = []

        def origin_for_status(p):
            origin = private_origin(p)
            # O push fica no bare local. Só a origem revalidada para o status recebe a URL sintética.
            if self.remote_head() == head:
                return url, origin[1], gate.rw.origin_identity(url)
            return origin

        def capture_gh(command, **kw):
            if command[0] != "gh":
                return run(command, **kw)
            gh_calls.append(command)
            return (0, "") if command[:7] == expected else (1, "endereço inesperado")

        with mock.patch.object(store, "lean_mode", return_value="auto"), \
                mock.patch.object(gate, "_private_origin", side_effect=origin_for_status), \
                mock.patch.object(self.effects, "status", side_effect=lambda *a, **kw: REAL_STATUS(self.effects, *a, **kw)), \
                mock.patch.object(store, "run", side_effect=capture_gh):
            out = self.publish()
        self.assertEqual([args[:7] for args in gh_calls], [expected])
        self.assertIn("context=local/ci", gh_calls[0])
        self.assertEqual((gate.exit_code(out), out["commit"], self.remote_head(),
                          self.w.git(self.w.live, "rev-parse", "HEAD")), (0, head, head, head), out)

    def test_origin_change_after_push_cannot_redirect_status_or_advance(self):
        head = self.edit()
        push = self.effects.push_private
        w = self.w

        def replace(p, contract):
            result = push(p, contract)
            w.git(self.wt, "remote", "set-url", "origin", f"https://other.example/{SLUG}.git")
            return result

        run = store.run

        def no_wrong_fetch(command, **kw):
            if "fetch" in command:
                self.assertEqual(w.git(command[2], "remote", "get-url", "origin"), str(w.remote))
            return run(command, **kw)

        with mock.patch.object(store, "lean_mode", return_value="auto"), \
                mock.patch.object(self.effects, "push_private", side_effect=replace), \
                mock.patch.object(store, "run", side_effect=no_wrong_fetch):
            out = self.publish()
        self.assertEqual((out["resultado"], out["instalacao"], out["commit"], self.remote_head()),
                         ("publicado", "status-falhou", head, head), out)
        self.status.assert_not_called()
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), self.base)

    def test_attributes_in_scope_still_hold(self):
        self.edit(path=f"{PASTA}/.gitattributes", text="SKILL.md -diff")
        self.assertIn(".gitattributes", self.held("escopo"))

    def test_marker_and_coauthor_guards(self):
        w = self.w
        self.edit()
        w.git(self.wt, "commit", "-q", "--amend", "-m", "Sem marca")
        self.held("sem-marca")
        w.git(self.wt, "commit", "-q", "--amend", "-m", "Com coautoria",
              "-m", "Retrofit-Mode: autonomous", "-m", "Co-authored-by: Fixture")
        self.held("coautoria")

    def test_description_requires_owner(self):
        path = f"{PASTA}/SKILL.md"
        md = self.wt / path
        md.write_text(md.read_text().replace("description: t", "description: outro gatilho"))
        self.edit()
        self.held("muda-description")

    def test_push_runs_hook_again_and_keeps_failure(self):
        self.edit()
        push = self.effects.push_private

        def reject(p, contract):
            with mock.patch.dict(os.environ, RW_FAKE_GATE_RC="2"):
                return push(p, contract)

        with mock.patch.object(store, "lean_mode", return_value="auto"), \
                mock.patch.object(self.effects, "push_private", side_effect=reject):
            out = self.publish()
        self.assertEqual((out["motivo"], self.remote_head()), ("push", self.base), out)
        self.assertEqual([x["rc"] for x in self.logs()], [0, 2])
        self.status.assert_not_called()

    def test_head_race_after_rehearsal_does_not_push(self):
        self.edit()
        push = self.effects.push_private

        def change_after_check(p, contract):
            self.w.git(self.wt, "commit", "--allow-empty", "-qm", "Troca de HEAD")
            return push(p, contract)

        with mock.patch.object(store, "lean_mode", return_value="auto"), \
                mock.patch.object(self.effects, "push_private", side_effect=change_after_check):
            out = self.publish()
        self.assertEqual((out["motivo"], self.remote_head()), ("push", self.base), out)
        self.assertEqual(len(self.logs()), 1)
        self.status.assert_not_called()

    def test_npm_precedes_the_effective_hook(self):
        self.w.commit_on_origin({"package-lock.json": "{}"}, "Adiciona lockfile")
        # O checkout do lote acompanha a base e recebe os scripts de gate já versionados.
        self.w.git(self.wt, "fetch", "origin")
        self.w.git(self.wt, "rebase", "origin/main")
        self.base = self.remote_head()
        self.w.gate_log.unlink()
        self.edit()
        new = self.w.tmp / "hooks-preparados"
        new.mkdir()
        self.w.git(self.wt, "config", "core.hooksPath", str(new))
        run = store.run

        def npm(command, *args, **kwargs):
            if list(command[:2]) == ["npm", "ci"]:
                self.assertEqual(kwargs["cwd"], self.wt)
                hook = new / "pre-push"
                hook.write_bytes((self.wt / ".githooks/pre-push").read_bytes())
                hook.chmod(0o755)
                return 0, "preparado"
            return run(command, *args, **kwargs)

        with mock.patch.object(store, "run", side_effect=npm):
            self.held("auto-dry")
        self.assertEqual(len(self.logs()), 1)
        self.w.gate_log.unlink()

        def npm_changes_origin(command, *args, **kwargs):
            if list(command[:2]) == ["npm", "ci"]:
                self.w.git(self.wt, "remote", "set-url", "origin", f"https://other.example/{SLUG}.git")
                return 0, "preparado"
            self.assertNotIn("ls-remote", command)
            return run(command, *args, **kwargs)

        with mock.patch.object(store, "run", side_effect=npm_changes_origin):
            self.assertIn("origin de fetch e push", self.held("gate"))
        self.assertFalse(self.w.gate_log.exists())
        with mock.patch.object(store, "run", side_effect=npm_changes_origin) as calls:
            with self.assertRaisesRegex(store.StoreError, "origin de fetch e push"):
                gate._rehearse(gate._Porta(self.ctx, self.rid, SKILL, []))
        self.assertFalse(any(call.args[0][:2] == ["npm", "ci"] for call in calls.call_args_list))

    def test_manual_declined_leaves_bare_and_clone_untouched(self):
        self.manual_retro(False)
        self.assertEqual(self.remote_head(), self.base)
        self.assertEqual(self.w.git(self.w.live, "rev-parse", "HEAD"), self.base)
        self.assertFalse(self.w.gate_log.exists())
        self.status.assert_not_called()

    def test_manual_confirmed_uses_prepush_and_advances(self):
        self.manual_retro(True)
        sha = self.remote_head()
        self.assertNotEqual(sha, self.base)
        self.assertEqual(self.w.git(self.w.live, "rev-parse", "HEAD"), sha)
        self.assertEqual(self.logs()[0]["stdin"], f"HEAD {sha} refs/heads/main {self.base}\n")
        self.status.assert_called_once_with(SLUG, sha, mock.ANY, host="localhost")

    def manual_retro(self, confirmed):
        w = self.w
        wt = w.tmp / "retro-manual"
        w.git(w.live, "fetch", "origin")
        w.git(w.live, "worktree", "add", "-qb", "retro-manual", str(wt), "origin/main")
        self.assertEqual(w.git(wt, "remote", "get-url", "--push", "origin"), str(w.remote))
        (wt / PASTA / "CHANGELOG.md").write_text("# Histórico\n\n## 2026-11-27\n\n- Retro manual.\n")
        if not confirmed:
            return
        w.git(wt, "commit", "-qam", "Registra lição manual")
        self.assertTrue(os.access(wt / w.git(wt, "rev-parse", "--git-path", "hooks/pre-push"), os.X_OK))
        w.git(wt, "push", "--no-follow-tags", "origin", "HEAD:main")
        self.effects.status(SLUG, w.git(wt, "rev-parse", "HEAD"), "gate verde", host="localhost")
        self.assertEqual(store.live_advance(self.ctx, SLUG)["resultado"], "ok")

    def test_retry_recovers_the_receipt_if_the_effect_did_not_return(self):
        head = self.edit()
        push = self.effects.push_private

        def interrupt_after_push(p, contract):
            self.assertTrue(push(p, contract)[0])
            raise OSError("interrompido após o push")

        with mock.patch.object(store, "lean_mode", return_value="auto"), \
                mock.patch.object(self.effects, "push_private", side_effect=interrupt_after_push):
            self.publish()
        self.assertEqual(self.remote_head(), head)
        self.status.assert_not_called()
        out = self.publish()
        self.assertEqual((gate.exit_code(out), out["commit"]), (0, head), out)
        self.status.assert_called_once_with(SLUG, head, "pre-push real: saída indisponível", host="localhost")
        self.assertEqual(len(self.logs()), 2)

    def test_window_and_revert_rehearse_again_without_publishing(self):
        w = self.w
        old = {file: w.git(w.remote, "show", f"{self.base}:{file}", strip=False)
               for file in (f"{PASTA}/SKILL.md", f"{PASTA}/CHANGELOG.md")}
        for n in range(10):
            w.advance_origin({"docs/teste.md": f"prova {n}\n"}, f"Publica {n}{MARK}", iso(T0))
        w.git(w.store, "fetch", "origin")
        sha = self.edit()
        bindir = w.tmp / "status-bin"
        bindir.mkdir()
        log = w.tmp / "status.json"
        gh = bindir / "gh"
        gh.write_text(f"#!{sys.executable}\n"
                      'import json, os, sys\n'
                      'with open(os.environ["RW_STATUS_LOG"], "w") as file:\n'
                      '    json.dump(sys.argv[1:], file)\n')
        gh.chmod(0o755)
        run = store.run
        with mock.patch.dict(os.environ, PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}", RW_STATUS_LOG=str(log)), \
                mock.patch.object(self.effects, "status", lambda *args, **kw: REAL_STATUS(self.effects, *args, **kw)), \
                mock.patch.object(store, "run", wraps=run) as called:
            out = self.publish()
        args = json.loads(log.read_text())
        self.assertEqual(args[:4], ["api", "-X", "POST", f"repos/{SLUG}/statuses/{sha}"])
        self.assertEqual(args[4:6], ["--hostname", "localhost"])
        self.assertIn("context=local/ci", args)
        self.assertIn("state=success", args)
        self.assertIn("gate: 0 passo(s)", args[-1])
        self.assertEqual((gate.exit_code(out), self.remote_head(), out["commit"]), (0, sha, sha), out)
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), sha)
        self.assertFalse(any("--no-verify" in call.args[0] for call in called.call_args_list))

        reverted = w.commit_on_origin(old, f"Reverte\n\nThis reverts commit {sha}.")
        self.open_batch()
        self.edit()
        self.assertIn("gate: 0 passo(s)", self.held("auto-dry"))
        self.assertEqual(self.remote_head(), reverted)

    def test_private_request_is_bound_to_origin(self):
        self.edit()
        pedido = auto.retro_pedido(self.ctx, self.rid)
        pedido["skills"][0]["repo"] = "fixture/outro"
        auto._write_json(self.folder / "pedido.json", pedido)
        self.held("fora-do-pedido")

    def test_private_requires_independent_first_pass(self):
        self.edit()
        (self.folder / "veredito.json").unlink()
        self.held("sem-veredito")

    def test_private_respects_session_cap(self):
        self.edit()
        self.w.config(auto_limits={"per_skill": 1, "per_session": 1})
        self.ctx = self.w.ctx()
        auto.append_registry(self.ctx, auto._line("s1", "outra-retro", "outra-retro/skill", "skill", [1],
                                                  "publicado", None, lote="skill"))
        self.held("teto")

    def test_private_uses_store_auditor(self):
        self.edit(text="Um caminho de máquina: " + "/".join(("", "Users", "fixture-user", "estado")))
        changed = self.w.store / gate.AUDITOR
        self.w.advance_origin({str(gate.AUDITOR): "raise SystemExit(42)\n"}, "Quebra auditor da fixture")
        self.w.git(self.w.store, "fetch", "origin")
        self.assertTrue(changed.is_file())
        # Um caminho absoluto em SKILL.md é avaliado antes da auditoria pela camada 1.
        self.held("caminho")
        auto.approve(self.ctx, self.rid, SKILL)
        self.assertIn("saiu 42", self.held("auditoria"))

    def test_manual_mode_stops_even_a_previously_approved_patch(self):
        self.edit()
        self.held("auto-dry")
        auto.approve(self.ctx, self.rid, SKILL)
        self.w.config(mode="manual")
        self.ctx = self.w.ctx()
        self.held("auto-dry")

    def test_private_changes_during_gate_hold_before_push(self):
        self.edit()
        rehearse = gate._rehearse

        def change(p):
            contract = rehearse(p)
            self.w.git(self.wt, "commit", "--allow-empty", "-qm", "Outro HEAD depois do ensaio")
            return contract

        with mock.patch.object(store, "lean_mode", return_value="auto"), \
                mock.patch.object(gate, "_rehearse", side_effect=change):
            self.held("arvore-suja")

    def test_dirt_and_additional_commit_cannot_publish(self):
        w = self.w
        self.edit()
        extra = self.wt / "fora"
        extra.touch()
        with mock.patch.object(store, "_live_fetch", wraps=store._live_fetch) as fetch:
            self.held("arvore-suja")
        fetch.assert_not_called()
        extra.unlink()
        w.git(self.wt, "commit", "--allow-empty", "-qm", "Um segundo commit")
        self.held("escopo")

    def test_reviewer_can_hold_a_nonpublishable_lesson(self):
        self.edit()
        path = self.folder / "veredito.json"
        reviews = json.loads(path.read_text())
        reviews["licoes"][0]["generica"] = False
        auto._write_json(path, reviews)
        self.held("nao-publicavel")

    def test_new_assets_need_audit_phase(self):
        assets = self.wt / PASTA / "assets"
        assets.mkdir()
        md = self.wt / PASTA / "SKILL.md"
        with md.open("a") as fh:
            fh.write("\nConsulte [o exemplo](assets/nota.md).\n")
        self.edit(path=f"{PASTA}/assets/nota.md", text="Dados de exemplo.")
        self.assertIn("self-containment", self.held("fase-de-auditoria"))
        patch = store.seal(self.ctx, self.rid, SKILL, [1], ["self-containment"])["patch"]
        self.assertEqual(auto.load_diff(self.lot / "diff.json")["patch"], patch)
        self.held("auto-dry")

    def test_rebase_rehearses_and_publishes_the_rebased_head(self):
        reviewed = self.edit()
        new_base = self.w.commit_on_origin({"README.md": "Documento fora do lote"}, "Avança a main")
        self.w.gate_log.unlink()
        with mock.patch.object(store, "lean_mode", return_value="auto"):
            out = self.publish()
        head = self.remote_head()
        self.assertNotEqual(head, reviewed)
        self.assertEqual((gate.exit_code(out), out["commit"]), (0, head), out)
        self.assertEqual(self.w.git(self.w.remote, "rev-parse", "main^"), new_base)
        self.assertEqual(self.logs()[-2:], [self.logs()[-1]] * 2)
