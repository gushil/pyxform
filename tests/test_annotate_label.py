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
            # xml__contains=["<label>Name\n", "[type: string] [name: name]</label>"],
            xml__contains=["[Name: name] [Type: string]</label>"],
            annotate=["type", "name"],
        )

    def test_not_annotated_label(self):
        """Test not to annotated label if there is no annotate argument."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=["<label>Name</label>"],
        )

    def test_annotated_label_contains_newline(self):
        """Test annotated label contains newline after user defined label."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=["<label>Name\n"],
            annotate=["type"],
        )

    def test_annotated_label_with_underscore(self):
        """Test annotated label with underscore."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |            |       |
            |        | type   | name       | label |
            |        | string | field_name | Name  |
            """,
            xml__contains=[r"[Name: field\_name] [Type: string]</label>"],
            annotate=["type", "name"],
        )

    def test_annotate_label__for_select_one(self):
        """Test annotated label for select one item."""
        self.assertPyxformXform(
            md="""
            | survey   |                     |      |       |
            |          | type                | name | label |
            |          | select_one choices1 | a    | A     |
            | choices  |                     |      |       |
            |          | list_name           | name | label |
            |          | choices1            | 1    | One   |
            |          | choices1            | 2    | Two   |
            """,
            xml__contains=[r"[Name: a] [Type: select\_one choices1]</label>"],
            annotate=["type", "name"],
        )

    def test_annotate_label__for_select_multiple(self):
        """Test annotated label for select multiple item."""
        self.assertPyxformXform(
            md="""
            | survey   |                          |      |       |
            |          | type                     | name | label |
            |          | select_multiple choices1 | a    | A     |
            | choices  |                          |      |       |
            |          | list_name                | name | label |
            |          | choices1                 | 1    | One   |
            |          | choices1                 | 2    | Two   |
            """,
            xml__contains=[r"[Name: a] [Type: select\_multiple choices1]</label>"],
            annotate=["type", "name"],
        )

    def test_not_annotate_label__for_choices(self):
        """Test not to annotated label for choices."""
        self.assertPyxformXform(
            md="""
            | survey   |                          |      |       |
            |          | type                     | name | label |
            |          | select_one choices1      | a    | A     |
            | choices  |                          |      |       |
            |          | list_name                | name | label |
            |          | choices1                 | 1    | One   |
            |          | choices1                 | 2    | Two   |
            """,
            xml__contains=["<label>One</label>", "<value>1</value>"],
            annotate=["type", "name"],
        )
