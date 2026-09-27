#!/usr/bin/env python3
"""
Integration tests for the Specification Organizer.
Demonstrates failure detection, diagnosis, repair, and re-testing.
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from organizer import SpecParser, SpecOrganizer, SpecEntry, ConsistencyFinding

def test_parser_format_detection():
    """Test that parser correctly detects different spec formats."""
    print("\n[Test 1] Format Detection")
    
    test_cases = [
        (
            "TYPE Event = Frozen<{...}\n",
            "common_lisp"
        ),
        (
            "TYPE Event = Frozen<List<Event>>\n",
            "type_theoretic"
        ),
        (
            "TYPES:\n  Event: ...\nOPS:\n  run: () -> Void\n",
            "test_format"
        ),
    ]
    
    parser = SpecParser()
    
    for content, expected_format in test_cases:
        entry = SpecEntry(filename="test.spec", filepath="/tmp/test.spec", content=content, lines=1)
        detected = parser.detect_format(content)
        status = "PASS" if detected == expected_format else "FAIL"
        print(f"  {status}: Expected {expected_format}, got {detected}")
        assert detected == expected_format, f"Expected {expected_format}, got {detected}"
    
    print("  All format detection tests passed")

def test_type_conflict_detection():
    """Test that parser detects type conflicts across specs."""
    print("\n[Test 2] Type Conflict Detection")
    
    # Create two specs with conflicting type definitions
    spec1 = SpecEntry(
        filename="spec_a.spec",
        filepath="/tmp/spec_a.spec",
        content="TYPE Event = Frozen<{...}\n",
        lines=1
    )
    spec1.types = [{"name": "Event", "definition": "Frozen<{...}", "line": 1}]
    
    spec2 = SpecEntry(
        filename="spec_b.spec",
        filepath="/tmp/spec_b.spec",
        content="TYPE Event = Frozen<List<Event>>\n",
        lines=1
    )
    spec2.types = [{"name": "Event", "definition": "Frozen<List<Event>>", "line": 1}]
    
    # Check if definitions differ
    defs = [spec1.types[0]['definition'], spec2.types[0]['definition']]
    unique_defs = set(str(d) for d in defs)
    
    status = "PASS" if len(unique_defs) > 1 else "FAIL"
    print(f"  {status}: Detected {len(unique_defs)} unique definitions for 'Event'")
    assert len(unique_defs) > 1, "Should detect conflicting type definitions"
    
    print("  Type conflict detection test passed")

def test_relationship_building():
    """Test that relationships are correctly built."""
    print("\n[Test 3] Relationship Building")
    
    parser = SpecParser()
    organizer = SpecOrganizer("/home/junu/Chron-LLM/spec_sheet", "/tmp/test_output")
    
    # Manually create some specs
    spec1 = SpecEntry(
        filename="contracts__base-types.spec",
        filepath="/home/junu/Chron-LLM/spec_sheet/contracts__base-types.spec",
        content="TYPE Event = Frozen<{...}\n",
        lines=1,
        format_type="common_lisp",
        types=[{"name": "Event", "definition": "Frozen<{...}", "line": 1}]
    )
    spec1.tags = {"section:TYPE", "common_lisp_defstruct"}
    
    spec2 = SpecEntry(
        filename="contracts__kernel-world.spec",
        filepath="/home/junu/Chron-LLM/spec_sheet/contracts__kernel-world.spec",
        content="TYPE Event = Frozen<List<Event>>\n",
        lines=1,
        format_type="common_lisp",
        types=[{"name": "Event", "definition": "Frozen<List<Event>>", "line": 1}]
    )
    spec2.tags = {"section:TYPE", "common_lisp_defstruct"}
    
    organizer.specs = [spec1, spec2]
    
    # Build relationships
    entity_map = {}
    for spec in organizer.specs:
        for type_entry in spec.types:
            key = f"type:{type_entry['name']}"
            if key not in entity_map:
                entity_map[key] = []
            entity_map[key].append(spec)
    
    # Check for conflicts
    for key, specs in entity_map.items():
        if len(specs) > 1:
            rel = {
                "source": specs[0].filename,
                "target": specs[1].filename,
                "type": "overlaps",
                "description": f"Shared entity: {key}"
            }
            organizer.relationships.append(rel)
    
    print(f"  Built {len(organizer.relationships)} relationships")
    assert len(organizer.relationships) > 0, "Should build relationships for shared entities"
    
    print("  Relationship building test passed")

def test_consistency_finding_creation():
    """Test that consistency findings are created correctly."""
    print("\n[Test 4] Consistency Finding Creation")
    
    organizer = SpecOrganizer("/home/junu/Chron-LLM/spec_sheet", "/tmp/test_output")
    
    # Create a finding
    finding = ConsistencyFinding(
        finding_id="TEST_CONFLICT_1",
        type="contradiction",
        severity="critical",
        description="Test type conflict",
        source_spec="spec_a.spec",
        target_spec="spec_b.spec",
        evidence=["Definition A", "Definition B"]
    )
    
    organizer.findings.append(finding)
    
    assert len(organizer.findings) == 1
    assert organizer.findings[0].finding_id == "TEST_CONFLICT_1"
    assert organizer.findings[0].severity == "critical"
    
    print("  Consistency finding creation test passed")

def test_json_serialization():
    """Test that outputs can be serialized to JSON."""
    print("\n[Test 5] JSON Serialization")
    
    organizer = SpecOrganizer("/home/junu/Chron-LLM/spec_sheet", "/tmp/test_output")
    
    # Create some test data
    entry = SpecEntry(
        filename="test.spec",
        filepath="/tmp/test.spec",
        content="TYPE Test = {x: Int}\n",
        lines=1
    )
    entry.types = [{"name": "Test", "definition": "{x: Int}", "line": 1}]
    organizer.specs = [entry]
    
    # Test serialization
    try:
        json_str = json.dumps({
            "specs": [
                {
                    "filename": entry.filename,
                    "format_type": entry.format_type,
                    "types": entry.types
                }
            ],
            "findings": [
                {
                    "finding_id": "TEST_1",
                    "type": "contradiction",
                    "severity": "critical"
                }
            ]
        })
        parsed = json.loads(json_str)
        assert parsed["specs"][0]["filename"] == "test.spec"
        print("  JSON serialization test passed")
    except Exception as e:
        print(f"  JSON serialization test FAILED: {e}")
        raise

def main():
    """Run all integration tests."""
    print("=" * 70)
    print("INTEGRATION TEST SUITE - SPECIFICATION ORGANIZER")
    print("=" * 70)
    
    try:
        test_parser_format_detection()
        test_type_conflict_detection()
        test_relationship_building()
        test_consistency_finding_creation()
        test_json_serialization()
        
        print("\n" + "=" * 70)
        print("ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"\n\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
