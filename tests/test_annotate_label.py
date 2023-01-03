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
            xml__contains=["[Name: name] ", "[Type: string] "],
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
            xml__not_contains=["[Name: name] ", "[Type: string] "],
        )

    def test_annotated_label_contains_newline(self):
        """Test annotated label contains newline."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=["<h:br/>"],
            annotate=["type"],
        )

    def test_annotated_label_with_underscore_field_name(self):
        """Test annotated label with underscore field name."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |            |       |
            |        | type   | name       | label |
            |        | string | field_name | Name  |
            """,
            xml__contains=[r"[Name: field\_name]"],
            annotate=["type", "name"],
        )

    def test_annotated_label_with_underscore_label_name(self):
        """Test annotated label with underscore label name."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |            |             |
            |        | type   | name       | label       |
            |        | string | field_name | Label_name  |
            """,
            xml__contains=[r"Label\_name"],
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
            xml__contains=[r"[Type: select\_one choices1]"],
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
            xml__contains=[r"[Type: select\_multiple choices1]"],
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
            xml__contains=["One [1]", "<value>1</value>"],
            annotate=["type", "name"],
        )

    def test_annotate_label__for_choices__with_underscore_in_label(self):
        """
        Test to annotated label for choices with underscore in label.
        Will not prepend the undercore with backslash
        """
        self.assertPyxformXform(
            md="""
            | survey   |                          |      |           |
            |          | type                     | name | label     |
            |          | select_one choices1      | a    | A         |
            | choices  |                          |      |           |
            |          | list_name                | name | label     |
            |          | choices1                 | 1    | Label_One |
            |          | choices1                 | 2_   | Two       |
            """,
            xml__contains=[r"Label_One [1]", r"Two [2_]"],
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
            xml__contains=[r"Label [One]"],
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
            xml__contains=["[Name: name]", "[Type: string]"],
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
            xml__contains=["[Name: name]", "[Type: string]"],
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
            xml__contains=[r"This is info: $[check1] / $[check2]"],
            annotate=["all"],
        )

    def test_annotated_label__body_class(self):
        """
        Test annotated label.
        Form body class always contains text-no-transform.
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | string |   name   | Name  |
            """,
            xml__contains=['<h:body class="no-text-transform">'],
            annotate=["all"],
        )

    def test_annotated_label__body_class_existing_style(self):
        """
        Test annotated label with existing style.
        Form body class always contains text-no-transform.
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |        |          |       |
            |          | type   |   name   | label |
            |          | string |   name   | Name  |
            | settings |        |          |       |
            |          | style      |      |       |
            |          | theme-grid |      |       |
            """,
            xml__contains=['<h:body class="theme-grid no-text-transform">'],
            annotate=["all"],
        )

    def test_annotated_label__body_class_existing_style_no_text_transform(self):
        """
        Test annotated label with no-text-transform in existing style.
        Form body class always contains text-no-transform.
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |        |          |       |
            |          | type   |   name   | label |
            |          | string |   name   | Name  |
            | settings |        |          |       |
            |          | style                     |     |       |
            |          | pages no-text-transform   |     |       |
            """,
            xml__contains=['<h:body class="pages no-text-transform">'],
            annotate=["all"],
        )

    def test_annotated_label__group_appearance(self):
        """
        Test annotated label.
        Group appearance class always contains no-collapse.
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |             |         |         |
            |        | type        | name    | label   |
            |        | string      | name    | Name    |
            |        | begin group | group1  | Group 1 |
            |        | string      | address | Address |
            |        | end group   |         |         |
            """,
            xml__contains=['<group appearance="no-collapse" ref="/data/group1">'],
            annotate=["all"],
        )

    def test_annotated_label__group_existing_appearance(self):
        """
        Test annotated label.
        Group appearance class always contains no-collapse.
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |             |         |         |            |
            |        | type        | name    | label   | appearance |
            |        | string      | name    | Name    |            |
            |        | begin group | group1  | Group 1 | w5         |
            |        | string      | address | Address |            |
            |        | end group   |         |         |            |
            """,
            xml__contains=['<group appearance="w5 no-collapse" ref="/data/group1">'],
            annotate=["all"],
        )

    def test_annotated_label__group_existing_appearance_no_collapse(self):
        """
        Test annotated label.
        Group appearance class always contains no-collapse.
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |             |         |         |                |
            |        | type        | name    | label   | appearance     |
            |        | string      | name    | Name    |                |
            |        | begin group | group1  | Group 1 | w4 no-collapse |
            |        | string      | address | Address |                |
            |        | end group   |         |         |                |
            """,
            xml__contains=['<group appearance="w4 no-collapse" ref="/data/group1">'],
            annotate=["all"],
        )

    def test_annotated_label__repeat_appearance(self):
        """
        Test annotated label.
        Repeat appearance class doesn't contains no-collapse.
        """
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |              |         |          |
            |        | type         | name    | label    |
            |        | string       | name    | Name     |
            |        | begin repeat | repeat1 | repeat 1 |
            |        | string       | address | Address  |
            |        | end repeat   |         |          |
            """,
            xml__contains=['<repeat nodeset="/data/repeat1">'],
            annotate=["all"],
        )

    def test_annotated_label__itemgroup(self):
        """Test annotated label for item with itemgroup."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                    |
            |        | type   |   name   | label | bind::oc:itemgroup |
            |        | string |   name   | Name  | ItemGroup1         |
            """,
            xml__contains=["[Item Group: ItemGroup1]"],
            annotate=["all"],
        )

    def test_annotated_label__itemgroup_style(self):
        """Test annotated label style for item with itemgroup."""
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                    |
            |        | type   |   name   | label | bind::oc:itemgroup |
            |        | string |   name   | Name  | ItemGroup1         |
            """,
            xml__contains=[
                '<h:span style="color: blue">[Item Group: ItemGroup1] </h:span>'
            ],
            annotate=["all"],
        )
