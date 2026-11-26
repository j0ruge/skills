"""Jornada do Stop com transcript e estado em disco para a issue #12."""

import json
import unittest

import test_retrofit_watch as fixture


class StopAttributionJourney(fixture.HookHarness, unittest.TestCase):
    def test_late_metadata_after_an_external_skill_in_a_later_message(self):
        for source in ("linked", "missing", "empty"):
            with self.subTest(source=source):
                self.w = fixture.World()
                try:
                    ours, external = fixture.StopTest.identified_loads(
                        self, other_message="msg_2"
                    )
                    if source == "missing":
                        del ours[2]["sourceToolUseID"]
                    elif source == "empty":
                        ours[2]["sourceToolUseID"] = ""

                    self.write(ours[:2], external)
                    self.assertIsNone(self.run_hook())
                    state_path = self.w.data / "sessions/s1.json"
                    before = json.loads(state_path.read_text(encoding="utf-8"))
                    self.assertEqual(before["offset"], self.w.transcript.stat().st_size)
                    self.assertIsNone(before["current"])

                    self.write(ours[2:], fixture.tool(error=True))
                    result = self.run_hook()
                    print(f"{source}={'silêncio' if result is None else 'saída'}")
                    after = json.loads(state_path.read_text(encoding="utf-8"))
                    self.assertEqual(after["offset"], self.w.transcript.stat().st_size)
                    self.assertIsNone(result, "O segundo Stop deve continuar em silêncio")
                    self.assertIsNone(after["current"])
                    self.assertEqual(after["skills"], before["skills"])
                finally:
                    self.w.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
