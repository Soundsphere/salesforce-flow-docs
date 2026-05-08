from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from automation_doc_exporter.classification import classify_automation
from automation_doc_exporter.cli import display_output_path, resolve_output_path
from automation_doc_exporter.exporter import export_automation_markdown
from automation_doc_exporter.parser import collect_automation_documents


FLOW_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>60.0</apiVersion>
    <description>Sets renewal follow-up.</description>
    <label>Contract Renewal Follow-up</label>
    <processType>AutoLaunchedFlow</processType>
    <start>
        <object>Contract</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
        <filters>
            <field>Status</field>
            <operator>EqualTo</operator>
            <value><stringValue>Activated</stringValue></value>
        </filters>
    </start>
    <decisions>
        <name>Eligible</name>
        <label>Eligible for renewal?</label>
        <rules>
            <name>InsideWindow</name>
            <label>Inside 90 days</label>
            <conditions>
                <leftValueReference>$Record.Renewal_Date__c</leftValueReference>
                <operator>LessThanOrEqualTo</operator>
                <rightValue><elementReference>Formula_Ninety_Days</elementReference></rightValue>
            </conditions>
            <connector><targetReference>CreateTask</targetReference></connector>
        </rules>
    </decisions>
    <recordUpdates>
        <name>UpdateContract</name>
        <label>Update Contract</label>
        <object>Contract</object>
        <inputAssignments>
            <field>Renewal_Status__c</field>
            <value><stringValue>Pending Follow-up</stringValue></value>
        </inputAssignments>
    </recordUpdates>
    <actionCalls>
        <name>CreateNotification</name>
        <label>Create Renewal Notification</label>
        <actionName>Create_Renewal_Notification</actionName>
        <actionType>flow</actionType>
        <inputParameters>
            <name>recordId</name>
            <value><elementReference>$Record.Id</elementReference></value>
        </inputParameters>
    </actionCalls>
    <status>Active</status>
</Flow>
"""


PROCESS_BUILDER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>49.0</apiVersion>
    <label>Case Processor Status Auto</label>
    <processType>Workflow</processType>
    <processMetadataValues>
        <name>ObjectType</name>
        <value><stringValue>Case</stringValue></value>
    </processMetadataValues>
    <processMetadataValues>
        <name>TriggerType</name>
        <value><stringValue>onAllChanges</stringValue></value>
    </processMetadataValues>
    <processMetadataValues>
        <name>ObjectVariable</name>
        <value><stringValue>myVariable_current</stringValue></value>
    </processMetadataValues>
    <processMetadataValues>
        <name>OldObjectVariable</name>
        <value><stringValue>myVariable_old</stringValue></value>
    </processMetadataValues>
    <status>Active</status>
</Flow>
"""


INVOCABLE_PROCESS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>49.0</apiVersion>
    <label>Case Subprocess for Status Working</label>
    <processType>InvocableProcess</processType>
    <variables>
        <name>SObject</name>
        <dataType>SObject</dataType>
        <objectType>Case</objectType>
        <isInput>true</isInput>
    </variables>
    <variables>
        <name>SObjectId</name>
        <dataType>String</dataType>
        <isInput>true</isInput>
    </variables>
    <decisions>
        <name>myDecision</name>
    </decisions>
    <status>Active</status>
</Flow>
"""


WORKFLOW_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Workflow xmlns="http://soap.sforce.com/2006/04/metadata">
    <rules>
        <fullName>GreenhouseOffline</fullName>
        <active>true</active>
        <formula>ISCHANGED(Status__c)</formula>
        <triggerType>onCreateOrTriggeringUpdate</triggerType>
        <actions>
            <name>GreenhouseOffline</name>
            <type>Alert</type>
        </actions>
    </rules>
    <alerts>
        <fullName>GreenhouseOffline</fullName>
        <description>Greenhouse Off-line</description>
        <protected>false</protected>
        <recipients>
            <type>owner</type>
        </recipients>
        <senderType>CurrentUser</senderType>
        <template>unfiled$public/GreenhouseOffline</template>
    </alerts>
</Workflow>
"""


class ExporterTest(unittest.TestCase):
    def test_collects_flows_process_builder_and_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write(root / "force-app/main/default/flows/Contract_Renewal_Follow_Up.flow-meta.xml", FLOW_XML)
            self._write(root / "force-app/main/default/flows/Case_Processor_Status_Auto.flow-meta.xml", PROCESS_BUILDER_XML)
            self._write(root / "force-app/main/default/workflows/Greenhouse__c.workflow-meta.xml", WORKFLOW_XML)

            documents = collect_automation_documents(root)

            by_title = {doc.title: doc for doc in documents}
            self.assertEqual(by_title["Contract Renewal Follow-up"].automation_type, "Record-triggered Flow")
            self.assertEqual(by_title["Case Processor Status Auto"].automation_type, "Process Builder")
            self.assertEqual(by_title["Workflow: Greenhouse__c"].automation_type, "Workflow Rule")
            self.assertIn(
                "force-app/main/default/flows/Contract_Renewal_Follow_Up.flow-meta.xml",
                by_title["Contract Renewal Follow-up"].source_path,
            )

    def test_exports_single_deterministic_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write(root / "force-app/main/default/flows/Contract_Renewal_Follow_Up.flow-meta.xml", FLOW_XML)
            output = root / "docs/automation/evidence/salesforce-automation.md"

            summary = export_automation_markdown(root, output)
            markdown = output.read_text(encoding="utf-8")

            self.assertEqual(summary.flow_count, 1)
            self.assertEqual(summary.workflow_count, 0)
            self.assertIn("# Contract Renewal Follow-up", markdown)
            self.assertIn("## Automation identity", markdown)
            self.assertIn("**Metadata type:** Flow metadata", markdown)
            self.assertIn("**Automation type:** Record-triggered Flow", markdown)
            self.assertIn("**Classification confidence:** High", markdown)
            self.assertIn("processType = AutoLaunchedFlow", markdown)
            self.assertIn("start.triggerType = RecordAfterSave", markdown)
            self.assertIn("## Entry Criteria", markdown)
            self.assertIn("## Automation Logic", markdown)
            self.assertIn("## Data and Side Effects", markdown)
            self.assertIn("## Operational Trust", markdown)
            self.assertNotIn("Key Decisions", markdown)
            self.assertIn("condition 1: Status EqualTo Activated", markdown)
            self.assertIn("Decision element: Eligible for renewal? (Eligible)", markdown)
            self.assertIn("force-app/main/default/flows/Contract_Renewal_Follow_Up.flow-meta.xml", markdown)
            self.assertNotIn(temp_dir, markdown)

    def test_process_builder_fixture_is_not_documented_as_generic_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write(root / "force-app/main/default/flows/Case_Processor_Status_Auto.flow-meta.xml", PROCESS_BUILDER_XML)
            output = root / "docs/automation/evidence/salesforce-automation.md"

            export_automation_markdown(root, output)
            markdown = output.read_text(encoding="utf-8")

            self.assertIn("**Metadata type:** Flow metadata", markdown)
            self.assertIn("**Automation type:** Process Builder", markdown)
            self.assertIn("**Classification confidence:** High", markdown)
            self.assertIn("processMetadataValues.TriggerType = onAllChanges", markdown)

    def test_invocable_process_fixture_is_classified_as_legacy_invocable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write(root / "force-app/main/default/flows/Case_Subprocess.flow-meta.xml", INVOCABLE_PROCESS_XML)
            output = root / "docs/automation/evidence/salesforce-automation.md"

            export_automation_markdown(root, output)
            markdown = output.read_text(encoding="utf-8")

            self.assertIn("**Automation type:** Legacy invocable process / likely Process Builder subprocess", markdown)
            self.assertIn("**Classification confidence:** Medium", markdown)
            self.assertIn("variables.SObject = SObject / Case", markdown)

    def test_cli_output_dir_resolves_default_evidence_filename(self) -> None:
        root = Path("/repo")

        output = resolve_output_path(
            project_root=root,
            output=None,
            output_dir="docs/automation/evidence",
        )

        self.assertEqual(output, root / "docs/automation/evidence/salesforce-automation.md")

    def test_cli_output_file_overrides_output_dir(self) -> None:
        root = Path("/repo")

        output = resolve_output_path(
            project_root=root,
            output="custom/path.md",
            output_dir="docs/automation/evidence",
        )

        self.assertEqual(output, root / "custom/path.md")

    def test_cli_display_path_allows_absolute_output_outside_project(self) -> None:
        output = display_output_path(
            project_root=Path("/repo"),
            output_path=Path("/tmp/salesforce-automation.md"),
        )

        self.assertEqual(output, Path("/tmp/salesforce-automation.md"))

    def _write(self, path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


class ClassificationTest(unittest.TestCase):
    def test_rule_matching_by_exact_value_and_when_all(self) -> None:
        result = classify_automation(
            {"processType": "Workflow", "processMetadataValues": {"TriggerType": "onAllChanges"}},
            {
                "rules": [
                    {
                        "id": "process_builder",
                        "priority": 10,
                        "when_all": [{"path": "processType", "equals": "Workflow"}],
                        "classify_as": {
                            "metadata_type": "Flow metadata",
                            "automation_type": "Process Builder",
                            "classification_confidence": "high",
                        },
                        "evidence_paths": ["processType", "processMetadataValues.TriggerType"],
                    }
                ],
                "fallback": {"automation_type": "Fallback"},
            },
        )

        self.assertEqual(result.automation_type, "Process Builder")
        self.assertEqual(result.evidence, ("processType = Workflow", "processMetadataValues.TriggerType = onAllChanges"))

    def test_priority_order_uses_highest_matching_rule(self) -> None:
        config = {
            "rules": [
                {
                    "id": "low",
                    "priority": 1,
                    "when_all": [{"path": "processType", "equals": "AutoLaunchedFlow"}],
                    "classify_as": {"automation_type": "Autolaunched Flow"},
                },
                {
                    "id": "high",
                    "priority": 100,
                    "when_all": [{"path": "processType", "equals": "AutoLaunchedFlow"}],
                    "classify_as": {"automation_type": "Record-triggered Flow"},
                },
            ],
            "fallback": {"automation_type": "Fallback"},
        }

        result = classify_automation({"processType": "AutoLaunchedFlow"}, config)

        self.assertEqual(result.automation_type, "Record-triggered Flow")
        self.assertEqual(result.matched_rule_id, "high")

    def test_when_any_gt_and_fallback(self) -> None:
        config = {
            "rules": [
                {
                    "id": "screen",
                    "priority": 1,
                    "when_any": [
                        {"path": "processType", "equals": "Flow"},
                        {"path": "elementCounts.screens", "gt": 0},
                    ],
                    "classify_as": {"automation_type": "Screen Flow"},
                }
            ],
            "fallback": {"automation_type": "Flow / flow-based automation", "classification_confidence": "low"},
        }

        self.assertEqual(classify_automation({"elementCounts": {"screens": 1}}, config).automation_type, "Screen Flow")
        self.assertEqual(classify_automation({"processType": "Unknown"}, config).automation_type, "Flow / flow-based automation")


if __name__ == "__main__":
    unittest.main()
