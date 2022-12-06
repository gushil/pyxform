# -*- coding: utf-8 -*-
"""
Annotate label test module.
"""
from tests.pyxform_test_case import PyxformTestCase


class AnnotateLabelTest(PyxformTestCase):
    """Test annotate_label XLSForms."""

    def test_annotated_label(self):
        """Test annotated label."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=["<label>Name [type: string] [name: name]</label>"],
            annotate=True,
        )

    def test_not_annotated_label(self):
        """Test not annotated label."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=["<label>Name</label>"],
        )

    def test_annotated_label_with_underscore(self):
        """Test annotated label."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |            |       |
            |        | type   | name       | label |
            |        | string | field_name | Name  |
            """,
            xml__contains=[r"<label>Name [type: string] [name: field\_name]</label>"],
            annotate=True,
        )
