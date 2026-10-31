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


if __name__=="__main__":
    unittest.main()
