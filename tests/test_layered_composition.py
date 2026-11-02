import copy
import tempfile
import unittest
from pathlib import Path

from layered_composition import starter_composition, validate_composition
from production_library import ProductionLibrary


class LayeredCompositionTests(unittest.TestCase):
    def test_starter_is_valid_and_preserves_order(self):
        data = validate_composition(starter_composition())
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["layers"][0]["type"], "background")
        self.assertIn("timer", [layer["type"] for layer in data["layers"]])
        self.assertTrue(data["layers"][0]["locked"])

    def test_moving_visible_layers_is_saved_without_emitting(self):
        with tempfile.TemporaryDirectory() as root:
            db = ProductionLibrary(Path(root) / "producciones.json")
            comp = starter_composition()
            comp["layers"][1].update(x=400, y=220, w=530, h=190)
            comp["layers"][1]["text"] = "Una comunidad de todos"
            snapshot = db.apply({"action": "add", "item": {
                "type": "pantalla", "name": "Inicio propio", "data": comp}})
            item = snapshot["productions"][0]["items"][-1]
            self.assertEqual(item["data"]["layers"][1]["x"], 400)
            self.assertEqual(ProductionLibrary(Path(root) / "producciones.json")
                             .get_item(snapshot["active_id"], item["id"])["data"], item["data"])

    def test_invalid_coordinates_and_external_media_rejected(self):
        for change in ({"x": 1900}, {"w": 6000}, {"asset": "https://invalid.example/img.png"},
                       {"fill": "url(https://invalid.example)"}):
            comp = starter_composition()
            comp["layers"][1].update(change)
            with self.assertRaises(ValueError):
                validate_composition(comp)

    def test_duplicate_id_and_unsupported_properties_rejected(self):
        comp = starter_composition()
        comp["layers"][2]["id"] = comp["layers"][1]["id"]
        with self.assertRaises(ValueError):
            validate_composition(comp)
        comp = starter_composition()
        comp["layers"][2]["html"] = "<script>alert(1)</script>"
        with self.assertRaises(ValueError):
            validate_composition(comp)

    def test_background_must_be_unique_and_behind_other_layers(self):
        comp = starter_composition()
        comp["layers"].reverse()
        with self.assertRaisesRegex(ValueError, "único fondo"):
            validate_composition(comp)
        comp = starter_composition()
        comp["layers"].append({**comp["layers"][0], "id": "fondo2"})
        with self.assertRaisesRegex(ValueError, "único fondo"):
            validate_composition(comp)

    def test_local_media_allowed_and_versions_guarded(self):
        comp = starter_composition()
        comp["layers"][0]["asset"] = "/media/" + "a" * 32 + ".mp4"
        comp["layers"][4]["asset"] = "/logo_parroquial.png?v=123"
        self.assertEqual(validate_composition(comp)["layers"][0]["asset"], comp["layers"][0]["asset"])
        comp["version"] = 99
        with self.assertRaises(ValueError):
            validate_composition(comp)


if __name__ == "__main__":
    unittest.main()
