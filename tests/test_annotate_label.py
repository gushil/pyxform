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

    def test_annotated_label_with_underscore_name(self):
        """Test annotated label with underscore name."""
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

    def test_annotated_label_with_underscore_label(self):
        """Test annotated label with underscore label."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |            |             |
            |        | type   | name       | label       |
            |        | string | field_name | Label_name  |
            """,
            xml__contains=[r"<label>Label\_name"],
            annotate=["all"],
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

    def test_annotate_label__for_choices(self):
        """Test to annotated label for choices."""
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
            xml__contains=["<label>One [1]</label>", "<value>1</value>"],
            annotate=["type", "name"],
        )

    def test_annotate_label__for_choices__with_underscore_in_label(self):
        """Test to annotated label for choices with underscore in label."""
        self.assertPyxformXform(
            md="""
            | survey   |                          |      |           |
            |          | type                     | name | label     |
            |          | select_one choices1      | a    | A         |
            | choices  |                          |      |           |
            |          | list_name                | name | label     |
            |          | choices1                 | 1    | Label_One |
            |          | choices1                 | 2    | Two       |
            """,
            xml__contains=[r"<label>Label\_One [1]</label>"],
            annotate=["all"],
        )

    def test_annotate_label__for_choices__with_curly_bracket_in_label(self):
        """Test to annotated label for choices with curly bracket chars in label."""
        self.assertPyxformXform(
            md="""
            | survey   |                          |      |             |
            |          | type                     | name | label       |
            |          | select_one choices1      | a    | A           |
            | choices  |                          |      |             |
            |          | list_name                | name | label       |
            |          | choices1                 | 1    | Label {One} |
            |          | choices1                 | 2    | Two         |
            """,
            xml__contains=[r"<label>Label [One] [1]</label>"],
            annotate=["all"],
        )

    def test_annotated_label__input_equals_all(self):
        """Test annotated label with input equals "all"."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=["[Name: name] [Type: string]</label>"],
            annotate=["all"],
        )

    def test_annotated_label__input_contains_all(self):
        """Test annotated label with input contains "all"."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=["[Name: name] [Type: string]</label>"],
            annotate=["type", "all"],
        )

    def test_annotated_label_with_curly_bracket_char_in_label(self):
        """Test annotated label with ["{", "}"] char in label."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |           |            |                                       |             |
            |        | type      | name       | label                                 | calculation |
            |        | string    | field_name | Event_1                               |             |
            |        | calculate | check1     |                                       | 1+1         |
            |        | calculate | check2     |                                       | 2+1         |
            |        | note      | info       | This is info:  ${check1} / ${check2}  |             |
            """,
            xml__contains=[r"<label>This is info: $[check1] / $[check2]"],
            annotate=["all"],
        )
