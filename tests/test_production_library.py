import tempfile
import unittest
from pathlib import Path
from production_library import ProductionLibrary


class ProductionLibraryTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = Path(self.dir.name) / "producciones.json"
        self.library = ProductionLibrary(self.path)

    def test_examples_are_available_and_persisted(self):
        state = self.library.snapshot()
        self.assertEqual(state["productions"][0]["name"], "Producción de ejemplo")
        self.assertGreaterEqual(len(state["productions"][0]["items"]), 4)
        self.assertEqual(ProductionLibrary(self.path).snapshot(), state)

    def test_multiple_items_duplicate_edit_and_reorder(self):
        state = self.library.apply({"action":"create_production", "name":"Domingo"})
        pid = state["active_id"]
        for name in ("Celebrante","Lector"):
            state = self.library.apply({"action":"add", "item":{"type":"lower_third","name":name,"data":{"name":name,"role":"Participante"}}})
        items = state["productions"][-1]["items"]
        self.assertEqual(len(items), 2)
        first = items[0]["id"]
        state = self.library.apply({"action":"duplicate","item_id":first})
        self.assertEqual(len(state["productions"][-1]["items"]),3)
        self.library.apply({"action":"move","item_id":first,"index":2})
        self.assertEqual(self.library.snapshot()["productions"][-1]["items"][2]["id"], first)
        self.library.apply({"action":"update","item_id":first,"item":{"name":"Celebrante principal","enabled":False}})
        with self.assertRaises(ValueError):
            self.library.get_item(pid, first)

    def test_rejects_unknown_type_and_invalid_index(self):
        with self.assertRaises(ValueError):
            self.library.apply({"action":"add","item":{"type":"unknown","name":"X","data":{}}})
        item_id = self.library.snapshot()["productions"][0]["items"][0]["id"]
        with self.assertRaises(ValueError):
            self.library.apply({"action":"move","item_id":item_id,"index":-1})
        with self.assertRaises(ValueError):
            self.library.apply({"action":"add","item":{"type":"titulo","name":"X","data":{"html":"x"*15000}}})

    def test_social_rotation_playlist_settings_and_logos(self):
        state = self.library.snapshot()
        pid = state["active_id"]
        playlist = self.library.social_playlist(pid)
        self.assertEqual([item["network"] for item in playlist["items"]], ["instagram", "youtube"])
        self.assertEqual(playlist["settings"]["duration"], 7)
        self.library.apply({"action":"social_settings", "settings":{
            "duration": 8, "interval": 15, "loop": False, "placement": "directo"}})
        self.assertEqual(self.library.social_playlist(pid)["settings"]["interval"],15)
        self.assertFalse(self.library.social_playlist(pid)["settings"]["loop"])
        self.assertEqual(ProductionLibrary(self.path).social_playlist(pid)["settings"]["placement"], "directo")
        with self.assertRaises(ValueError):
            self.library.apply({"action":"social_settings", "settings":{"duration": 20, "interval": 4}})
        with self.assertRaises(ValueError):
            self.library.apply({"action":"add","item":{"type":"red_social","name":"Mala URL",
                "data":{"network":"instagram","handle":"@test","logo":"https://evil.example/tracker.png"}}})
        logo = "/media/" + "a" * 32 + ".webp"
        result=self.library.apply({"action":"add","item":{"type":"red_social","name":"Con imagen propia",
               "data":{"network":"facebook","handle":"Mi página","phrase":"Dale like","logo":logo}}})
        self.assertEqual(result["productions"][0]["items"][-1]["data"]["logo"], logo)

    def test_social_rotation_requires_enabled_item(self):
        state = self.library.apply({"action":"create_production","name":"Vacía"})
        with self.assertRaises(ValueError):
            self.library.social_playlist(state["active_id"])
        self.library.apply({"action":"add","item":{"type":"red_social","name":"Solo desactivada",
            "enabled":False,"data":{"network":"youtube","handle":"Mi canal","phrase":"Suscríbete","logo":""}}})
        with self.assertRaises(ValueError):
            self.library.social_playlist(state["active_id"])


if __name__=="__main__":
    unittest.main()
