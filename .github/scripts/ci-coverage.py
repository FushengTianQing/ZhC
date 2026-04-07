#!/usr/bin/env python3
"""从 coverage.xml 提取覆盖率百分比"""
import xml.etree.ElementTree as ET
import sys

try:
    t = ET.parse("coverage.xml").getroot()
    pct = float(t.attrib.get("line-rate", 0)) * 100
    print(f"{pct:.1f}%")
except Exception:
    print("N/A")
