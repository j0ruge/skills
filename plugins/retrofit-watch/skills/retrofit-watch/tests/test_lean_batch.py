"""A triagem e o selo vinculam o lote à skill rastreada na origem privada."""
from datetime import date
import json
import os
from pathlib import Path
from runpy import run_path
import unittest
from unittest import mock

from fixture_private import PASTA, SKILL, SLUG, PrivateWorld
import rw_auto as auto
import rw_store as store


class BatchTest(unittest.TestCase):
    def setUp(self):
        self.w = PrivateWorld()
        self.addCleanup(self.w.cleanup)
        self.ctx = self.w.ctx()

    def request(self, *lessons, collision=False):
        w = self.w
        rid = w.retro(list(lessons), [{} for _ in lessons])
        path = auto.retro_dir(self.ctx, rid) / "pedido.json"
        data = json.loads(path.read_text())
        data["skills"] = [{"key": "lean:fixture", "plugin": SKILL, "label": SKILL,
                           "skills": [SKILL], "repo": SLUG, "modo": "auto-dry"}]
        if collision:
            data["skills"].insert(0, {"key": f"full:{SKILL}", "plugin": SKILL, "label": SKILL,
                                      "skills": [SKILL]})
        auto._write_json(path, data)
        return rid

    def private(self, **fields):
        return dict({"plugin": SKILL, "repo": SLUG}, **fields)

    def test_lesson_must_match_origin_plugin_and_skill(self):
        self.w.config(lean_auto=[SLUG, "fixture/outro"])
        self.ctx = self.w.ctx()
        rid = self.request(self.private(), self.private(repo="fixture/outro"), self.private(repo=None),
                           self.private(skill="outra"), self.private(plugin="outro"))
        plan = auto.triage(self.ctx, rid)
        self.assertEqual([(batch["repo"], batch["licoes"]) for batch in plan["lotes"]], [(SLUG, [1])])
        self.assertEqual([(h["licoes"], h["motivo"]) for h in plan["segurar"]],
                         [([n], "fora-do-pedido") for n in range(2, 6)])
        self.w.config(lean_auto=[])
        self.assertEqual(auto.triage(self.w.ctx(), rid)["lotes"], [])

    def test_same_name_store_and_lean_never_merge(self):
        private, full = self.private(), {"plugin": SKILL}
        for first, second in ((private, full), (full, private), (private, full | {"muda_description": True})):
            with self.subTest(first=first):
                rid = self.request(first, second, collision=True)
                plan = auto.triage(self.ctx, rid)
                self.assertEqual([(b.get("repo"), b["licoes"]) for b in plan["lotes"]],
                                 [(first.get("repo"), [1])])
                self.assertEqual([(h["licoes"], h["motivo"], h["detalhe"]) for h in plan["segurar"]],
                                 [([2], "fora-do-pedido", "lote duplicado")])
                held = auto.read_registry(self.ctx)
                self.assertTrue(any(h["id"] == rid and h["resultado"] == "segurado"
                                    and h["detalhe"] == "lote duplicado" for h in held))

    def test_private_description_and_body_share_one_batch(self):
        rid = self.request(self.private(), self.private(muda_description=True))
        batches = auto.triage(self.ctx, rid)["lotes"]
        self.assertEqual([(b["lote"], b["tipo"], b["licoes"]) for b in batches],
                         [(SKILL, "description", [1, 2])])

    def test_prepare_uses_only_live_clone_and_latest_remote_base(self):
        w = self.w
        rid = self.request(self.private())
        base = w.commit_on_origin({"README.md": "nova revisão"}, "Atualiza base")
        w.git(w.dev, "switch", "-qc", "desenvolvimento")
        (w.dev / "estado").write_text("preservar")
        commands = (("show-ref",), ("status", "--porcelain"), ("worktree", "list", "--porcelain"))
        dev_before = [w.git(w.dev, *args) for args in commands]
        live_before = w.git(w.live, "rev-parse", "HEAD")
        lot = store.prepare(self.ctx, rid, SKILL)
        self.assertEqual((lot["repo"], lot["pasta"], lot["base"]), (SLUG, PASTA, base))
        self.assertEqual(Path(w.git(lot["worktree"], "rev-parse", "--git-common-dir")), w.live / ".git")
        self.assertEqual([w.git(w.dev, *args) for args in commands], dev_before)
        self.assertEqual(w.git(w.live, "rev-parse", "HEAD"), live_before)
        self.assertEqual(store.prepare(self.ctx, rid, SKILL), lot)

    def test_prepare_rejects_swapped_clone_missing_skill_and_symlink(self):
        w = self.w
        rid = self.request(self.private())
        w.git(w.live, "remote", "set-url", "origin", str(w.origin))
        with self.assertRaisesRegex(store.StoreError, "clone dedicado"):
            store.prepare(self.ctx, rid, SKILL)
        w.git(w.live, "remote", "set-url", "origin", str(w.remote))
        w.git(w.dev, "rm", f"{PASTA}/SKILL.md")
        w.git(w.dev, "commit", "-qm", "Tira a skill")
        w.git(w.dev, "push", "-q", "origin", "HEAD:main")
        with self.assertRaisesRegex(store.StoreError, "pasta"):
            store.prepare(self.ctx, rid, SKILL)
        os.symlink(w.ticket / "SKILL.md", w.dev / PASTA / "SKILL.md")
        w.git(w.dev, "add", f"{PASTA}/SKILL.md")
        w.git(w.dev, "commit", "-qm", "Um link não é uma skill rastreada")
        w.git(w.dev, "push", "-q", "origin", "HEAD:main")
        with self.assertRaisesRegex(store.StoreError, "pasta"):
            store.prepare(self.ctx, rid, SKILL)
        self.assertFalse(auto.lote_dir(self.ctx, rid, SKILL).exists())

    def test_prepare_rejects_ambiguous_tracked_folder(self):
        w = self.w
        rid = self.request(self.private())
        w.commit_on_origin({f"outra/{SKILL}/SKILL.md": "segunda candidata"}, "Duplica o nome")
        with self.assertRaisesRegex(store.StoreError, "ambígua"):
            store.prepare(self.ctx, rid, SKILL)

    def test_private_formats_reject_invalid_slug_and_paths(self):
        rid = self.request(self.private(repo="fixture/.."))
        with self.assertRaisesRegex(auto.Malformed, "repo"):
            auto.retro_licoes(self.ctx, rid)
        rid = self.request(self.private())
        lot = store.prepare(self.ctx, rid, SKILL)
        path = auto.lote_dir(self.ctx, rid, SKILL) / "retrofit.json"
        for fields in ({"repo": None}, {"repo": "fixture/.."}, {"pasta": "../fora"},
                       {"pasta": "/fora"}, {"pasta": "C:/fora"}, {"pasta": "a\\SKILL.md"}):
            with self.subTest(fields=fields):
                auto._write_json(path, lot | fields)
                with self.assertRaises(auto.Malformed):
                    auto.load_retrofit(path)
        auto._write_json(path, {k: v for k, v in lot.items() if k != "pasta"})
        with self.assertRaises(auto.Malformed):
            auto.load_retrofit(path)

    def test_seal_private_allows_name_and_email_but_checks_user_path_and_secret(self):
        w = self.w
        names = w.store / store.PRIVATE_LIST
        digest = run_path(str(w.store / store.NAME_CHECK))["resumo"]("Sintetica")
        w.advance_origin({store.PRIVATE_LIST: names.read_text() + "\n" + digest + "\n"},
                         "Adiciona nome sintético à lista da fixture")
        w.git(w.store, "fetch", "origin")
        rid = self.request(self.private(), self.private(repo="fixture/outro"))
        lot = store.prepare(self.ctx, rid, SKILL)
        wt = Path(lot["worktree"])
        changelog = wt / PASTA / "CHANGELOG.md"
        changelog.write_text(f"# Histórico\n\n## {date.today().isoformat()}\n\n- Lição da fixture.\n")
        w.git(wt, "add", "-A")
        email = "@".join(("contato", "exemplo.test"))
        w.git(wt, "commit", "-qm", f"Documenta Sintetica {email}",
              "-m", "Retrofit-Mode: autonomous")
        with self.assertRaisesRegex(store.StoreError, "licao 2"):
            store.seal(self.ctx, rid, SKILL, [2], [])
        with mock.patch.object(store, "worktree_path", return_value=w.dev):
            with self.assertRaisesRegex(store.StoreError, "não pertence ao clone dedicado"):
                store.seal(self.ctx, rid, SKILL, [1], [])
        sealed = store.seal(self.ctx, rid, SKILL, [1], [])
        self.assertEqual(sealed["camada1"], [])
        self.assertIsNone(sealed["versao"])
        self.assertEqual(sealed["patch"], store.patch_id(wt))
        self.assertEqual(sealed["commit"], w.git(wt, "rev-parse", "HEAD"))
        self.assertEqual(auto.load_retrofit(auto.lote_dir(self.ctx, rid, SKILL) / "retrofit.json")["patch"],
                         sealed["patch"])
        with changelog.open("a") as fh:
            user_path = "/".join(("", "home", "fixture-user", "estado"))
            fh.write(f"- {user_path}\n")
            fh.write("- " + "gh" + "p_" + "Z" * 12 + "\n")
        w.git(wt, "add", "-A")
        w.git(wt, "commit", "--amend", "--no-edit", "-q")
        findings = store.seal(self.ctx, rid, SKILL, [1], [])["camada1"]
        self.assertEqual({store.GATE_FINDING.fullmatch(f)[1] for f in findings}, {"caminho", "segredo"})
