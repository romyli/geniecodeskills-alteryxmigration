import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "inventory_alteryx.py"
SPEC = importlib.util.spec_from_file_location("inventory_alteryx", SCRIPT)
inventory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(inventory)


FIXTURE = """<?xml version="1.0"?>
<AlteryxDocument yxmdVer="2025.1">
  <Nodes>
    <Node ToolID="1">
      <GuiSettings Plugin="AlteryxGuiToolkit.ToolContainer.ToolContainer" />
      <Properties><Configuration><Disabled value="True" /></Configuration></Properties>
      <ChildNodes>
        <Node ToolID="2">
          <GuiSettings Plugin="AlteryxBasePluginsGui.DbFileInput.DbFileInput" />
          <Properties><Configuration><File FileFormat="0">C:\\inactive.csv</File></Configuration></Properties>
        </Node>
      </ChildNodes>
    </Node>
    <Node ToolID="3">
      <GuiSettings Plugin="AlteryxBasePluginsGui.Join.Join" />
      <Properties><Configuration>
        <JoinInfo connection="Left"><Field field="Area" /></JoinInfo>
        <JoinInfo connection="Right"><Field field="Field" /></JoinInfo>
        <SelectFields>
          <SelectField field="Left_Area" selected="True" input="Left_" />
          <SelectField field="Right_Field" selected="False" input="Right_" />
        </SelectFields>
      </Configuration></Properties>
    </Node>
    <Node ToolID="4">
      <GuiSettings Plugin="AlteryxBasePluginsGui.Union.Union" />
      <Properties><Configuration>
        <Mode>ByName</Mode>
        <ByName_OutputMode>All</ByName_OutputMode>
      </Configuration></Properties>
    </Node>
  </Nodes>
  <Connections>
    <Connection><Origin ToolID="2" Connection="Output" /><Destination ToolID="3" Connection="Left" /></Connection>
    <Connection><Origin ToolID="3" Connection="Join" /><Destination ToolID="4" Connection="Input" /></Connection>
  </Connections>
  <Properties>
    <Events>
      <Enabled value="True" />
      <Event>
        <Description>After errors email person@example.com</Description>
        <When>AfterError</When>
        <SendMail value="True" />
        <email_To>person@example.com</email_To>
      </Event>
    </Events>
  </Properties>
</AlteryxDocument>
"""


class InventoryAlteryxTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "fixture.yxmd"
        self.path.write_text(FIXTURE, encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_effective_activity_connections_and_events(self):
        result = inventory.analyze(self.path)

        self.assertEqual(result["node_count"], 4)
        self.assertEqual(result["active_node_count"], 2)
        self.assertEqual(result["active_connection_count"], 1)
        self.assertEqual(result["sources"], [])
        self.assertEqual(
            [item["tool_id"] for item in result["inactive_nodes"]], ["1", "2"]
        )
        self.assertEqual(
            result["events"],
            [
                {
                    "when": "AfterError",
                    "action": "email",
                    "enabled": True,
                    "contains_secret_material": False,
                }
            ],
        )

    def test_semantic_configuration_and_recipient_redaction(self):
        result = inventory.analyze(self.path)
        by_id = {item["tool_id"]: item for item in result["semantic_nodes"]}

        self.assertEqual(by_id["3"]["dropped_fields"], ["Right_Field"])
        self.assertEqual(
            by_id["3"]["join_keys"],
            [
                {"connection": "Left", "fields": ["Area"]},
                {"connection": "Right", "fields": ["Field"]},
            ],
        )
        self.assertEqual(
            by_id["4"]["union_settings"],
            {"Mode": "ByName", "ByName_OutputMode": "All"},
        )

        report = inventory.markdown_report([result])
        self.assertIn("AfterError: email (enabled)", report)
        self.assertNotIn("person@example.com", report)


if __name__ == "__main__":
    unittest.main()
