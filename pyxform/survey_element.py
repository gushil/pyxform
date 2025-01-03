# -*- coding: utf-8 -*-
"""
Survey Element base class for all survey elements.
"""
import json
import re
from functools import lru_cache
from typing import TYPE_CHECKING

from pyxform import constants
from pyxform.errors import PyXFormError
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.utils import (
    BRACKETED_TAG_REGEX,
    INVALID_XFORM_TAG_REGEXP,
    default_is_dynamic,
    node,
)
from pyxform.xls2json import print_pyobj_to_json
from pyxform.xlsparseutils import is_valid_xml_tag

if TYPE_CHECKING:
    from typing import List

    from pyxform.utils import DetachableElement


def _overlay(over, under):
    if type(under) == dict:
        result = under.copy()
        result.update(over)
        return result
    return over if over else under


class SurveyElement(dict):
    """
    SurveyElement is the base class we'll looks for the following keys
    in kwargs: name, label, hint, type, bind, control, parent,
    children, and question_type_dictionary.
    """

    # the following are important keys for the underlying dict that
    # describes this survey element
    FIELDS = {
        "name": str,
        constants.COMPACT_TAG: str,  # used for compact (sms) representation
        "sms_field": str,
        "sms_option": str,
        "label": str,
        "hint": str,
        "guidance_hint": str,
        "default": str,
        "type": str,
        "appearance": str,
        "parameters": dict,
        "intent": str,
        "jr:count": str,
        "bind": dict,
        "instance": dict,
        "control": dict,
        "media": dict,
        # this node will also have a parent and children, like a tree!
        "parent": lambda: None,
        "children": list,
        "itemset": str,
        "choice_filter": str,
        "query": str,
        "autoplay": str,
        "flat": lambda: False,
        "action": str,
        "list_name": str,
        "trigger": str,
        "annotated_fields": dict,
    }

    def _default(self):
        # TODO: need way to override question type dictionary
        defaults = QUESTION_TYPE_DICT
        return defaults.get(self.get("type"), {})

    def __getattr__(self, key):
        """
        Get attributes from FIELDS rather than the class.
        """
        if key in self.FIELDS:
            question_type_dict = self._default()
            under = question_type_dict.get(key, None)
            over = self.get(key)
            if not under:
                return over
            return _overlay(over, under)
        raise AttributeError(key)

    def __hash__(self):
        return hash(id(self))

    @property
    def __name__(self):
        return "SurveyElement"

    def __setattr__(self, key, value):
        self[key] = value

    def __init__(self, **kwargs):
        for key, default in self.FIELDS.items():
            self[key] = kwargs.get(key, default())
        self._link_children()

        # Create a space label for unlabeled elements with the label
        # appearance tag. # This is because such elements are used to label the
        # options for selects in a field-list and might want blank labels for
        # themselves.
        if self.control.get("appearance") == "label" and not self.label:
            self["label"] = " "

    def _link_children(self):
        for child in self.children:
            child.parent = self

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_children(self, children):
        if type(children) == list:
            for child in children:
                self.add_child(child)
        else:
            self.add_child(children)

    BINDING_CONVERSIONS = {
        "yes": "true()",
        "Yes": "true()",
        "YES": "true()",
        "true": "true()",
        "True": "true()",
        "TRUE": "true()",
        "no": "false()",
        "No": "false()",
        "NO": "false()",
        "false": "false()",
        "False": "false()",
        "FALSE": "false()",
    }

    CONVERTIBLE_BIND_ATTRIBUTES = (
        "readonly",
        "required",
        "relevant",
        "constraint",
        "calculate",
    )

    # Supported media types for attaching to questions
    SUPPORTED_MEDIA = ("image", "big-image", "audio", "video")

    OC_CUSTOM_ANNOTATION_PREFIX = "oc:oc_annotation_"

    def validate(self):
        if not is_valid_xml_tag(self.name):
            invalid_char = re.search(INVALID_XFORM_TAG_REGEXP, self.name)
            raise PyXFormError(
                f"The name '{self.name}' contains an invalid character '{invalid_char.group(0)}'. Names {constants.XML_IDENTIFIER_ERROR_MESSAGE}"
            )

    # TODO: Make sure renaming this doesn't cause any problems
    def iter_descendants(self):
        """
        A survey_element is a dictionary of survey_elements
        This method does a preorder traversal over them.
        For the time being this survery_element is included among its
        descendants
        """
        # it really seems like this method should not yield self
        yield self
        for e in self.children:
            for f in e.iter_descendants():
                yield f

    @lru_cache(maxsize=None)
    def any_repeat(self, parent_xpath):
        """Return True if there ia any repeat in `parent_xpath`."""
        for item in self.iter_descendants():
            if item.get_xpath() == parent_xpath and item.type == constants.REPEAT:
                return True

        return False

    def get_lineage(self):
        """
        Return a the list [root, ..., self._parent, self]
        """
        result = [self]
        current_element = self
        while current_element.parent:
            current_element = current_element.parent
            result = [current_element] + result
        # For some reason the root element has a True flat property...
        output = [result[0]]
        for item in result[1:]:
            if not item.get("flat"):
                output.append(item)
        return output

    def get_root(self):
        return self.get_lineage()[0]

    def get_xpath(self):
        """
        Return the xpath of this survey element.
        """
        return "/".join([""] + [n.name for n in self.get_lineage()])

    def get_abbreviated_xpath(self):
        lineage = self.get_lineage()
        if len(lineage) >= 2:
            return "/".join([str(n.name) for n in lineage[1:]])
        else:
            return lineage[0].name

    def _delete_keys_from_dict(self, dictionary: dict, keys: list):
        """
        Deletes a list of keys from a dictionary.
        Credits: https://stackoverflow.com/a/49723101
        """
        for key in keys:
            if key in dictionary:
                del dictionary[key]

        for value in dictionary.values():
            if isinstance(value, dict):
                self._delete_keys_from_dict(value, keys)

    def to_json_dict(self):
        """
        Create a dict copy of this survey element by removing inappropriate
        attributes and converting its children to dicts
        """
        self.validate()
        result = self.copy()
        to_delete = ["parent", "question_type_dictionary", "_created"]
        # Delete all keys that may cause a "Circular Reference"
        # error while converting the result to JSON
        self._delete_keys_from_dict(result, to_delete)
        children = result.pop("children")
        result["children"] = []
        for child in children:
            result["children"].append(child.to_json_dict())
        # remove any keys with empty values
        for k, v in list(result.items()):
            if not v:
                del result[k]

        return result

    def to_json(self):
        return json.dumps(self.to_json_dict())

    def json_dump(self, path=""):
        if not path:
            path = self.name + ".json"
        print_pyobj_to_json(self.to_json_dict(), path)

    def __eq__(self, y):
        return (
            hasattr(y, "to_json_dict")
            and callable(y.to_json_dict)
            and self.to_json_dict() == y.to_json_dict()
        )

    def _translation_path(self, display_element):
        return self.get_xpath() + ":" + display_element

    def get_translations(self, default_language):
        """
        Returns translations used by this element so they can be included in
        the <itext> block. @see survey._setup_translations
        """
        bind_dict = self.get("bind")
        if bind_dict and type(bind_dict) is dict:
            constraint_msg = bind_dict.get("jr:constraintMsg")
            if type(constraint_msg) is dict:
                for lang, text in constraint_msg.items():
                    yield {
                        "path": self._translation_path("jr:constraintMsg"),
                        "lang": lang,
                        "text": text,
                        "output_context": self,
                    }
            elif constraint_msg and re.search(BRACKETED_TAG_REGEX, constraint_msg):
                yield {
                    "path": self._translation_path("jr:constraintMsg"),
                    "lang": default_language,
                    "text": constraint_msg,
                    "output_context": self,
                }

            required_msg = bind_dict.get("jr:requiredMsg")
            if type(required_msg) is dict:
                for lang, text in required_msg.items():
                    yield {
                        "path": self._translation_path("jr:requiredMsg"),
                        "lang": lang,
                        "text": text,
                        "output_context": self,
                    }
            elif required_msg and re.search(BRACKETED_TAG_REGEX, required_msg):
                yield {
                    "path": self._translation_path("jr:requiredMsg"),
                    "lang": default_language,
                    "text": required_msg,
                    "output_context": self,
                }
            no_app_error_string = bind_dict.get("jr:noAppErrorString")
            if type(no_app_error_string) is dict:
                for lang, text in no_app_error_string.items():
                    yield {
                        "path": self._translation_path("jr:noAppErrorString"),
                        "lang": lang,
                        "text": text,
                        "output_context": self,
                    }

        for display_element in ["label", "hint", "guidance_hint"]:
            label_or_hint = self[display_element]

            if (
                display_element == "label"
                and self.needs_itext_ref()
                and type(label_or_hint) is not dict
                and label_or_hint
            ):
                label_or_hint = {default_language: label_or_hint}

            # always use itext for guidance hints because that's
            # how they're defined - https://opendatakit.github.io/xforms-spec/#languages
            if (
                display_element == "guidance_hint"
                and not (isinstance(label_or_hint, dict))
                and len(label_or_hint) > 0
            ):
                label_or_hint = {default_language: label_or_hint}

            # always use itext for hint if there's a guidance hint
            if (
                display_element == "hint"
                and not (isinstance(label_or_hint, dict))
                and len(label_or_hint) > 0
                and "guidance_hint" in self.keys()
                and len(self["guidance_hint"]) > 0
            ):
                label_or_hint = {default_language: label_or_hint}

            if type(label_or_hint) is dict:
                for lang, text in label_or_hint.items():
                    if display_element == "label":
                        annotated_label = self.get_annotated_label(lang)
                        if annotated_label != text:
                            text = annotated_label
                    yield {
                        "display_element": display_element,  # Not used
                        "path": self._translation_path(display_element),
                        "element": self,  # Not used
                        "output_context": self,
                        "lang": lang,
                        "text": text,
                    }

    def get_media_keys(self):
        """
        @deprected
        I'm leaving this in just in case it has outside references.
        """
        return {"media": "%s:media" % self.get_xpath()}

    def needs_itext_ref(self):
        return type(self.label) is dict or (
            type(self.media) is dict and len(self.media) > 0
        )

    def get_setvalue_node_for_dynamic_default(self, in_repeat=False):
        survey = self.get_root()
        if (
            not self.default
            or not default_is_dynamic(self.default, self.type)
            or (
                default_is_dynamic(self.default, self.type)
                and survey.is_annotated_form()
                and "default" in survey.annotated_fields
            )
        ):
            return None

        default_with_xpath_paths = survey.insert_xpaths(self.default, self)

        triggering_events = "odk-instance-first-load"
        if in_repeat:
            triggering_events += " odk-new-repeat"

        return node(
            "setvalue",
            ref=self.get_xpath(),
            value=default_with_xpath_paths,
            event=triggering_events,
        )

    def annotated_value_processing(self, value, field_name):

        # Prepend all underscores (_) with backslash (\)
        def prepend_underscore_with_backslash(value):
            underscore_str = "_"
            backslash_str = "\\"
            value = (backslash_str + underscore_str).join(value.split(underscore_str))

            return value

        attr_value = value
        if field_name in [
            "readonly",
            "external",
            "contactdata",
            "constraint_type",
            "required_type",
            "identifier",
        ]:
            return attr_value

        if field_name != "choices":
            if field_name == "label":
                refs_in_label = [
                    _.group() for _ in re.finditer(BRACKETED_TAG_REGEX, value)
                ]
                if len(refs_in_label) > 0:
                    for ref in refs_in_label:
                        prepended_ref = prepend_underscore_with_backslash(ref)
                        attr_value = attr_value.replace(ref, prepended_ref)
            else:
                attr_value = prepend_underscore_with_backslash(attr_value)

            if field_name in [
                "relevant",
                "required",
                "constraint",
                "default",
                "choice_filter",
                "calculation",
                "trigger",
                "repeat_count",
                "custom",
            ]:
                # Replace > with gt
                attr_value = attr_value.replace(">", "gt")

                # Replace < with lt
                attr_value = attr_value.replace("<", "lt")

            if field_name in [
                "relevant",
                "constraint",
                "default",
                "calculation",
                "required",
                "custom",
            ]:
                # Prepend * with \
                attr_value = attr_value.replace("*", "\*")  # noqa

        # Replace { with [
        attr_value = attr_value.replace("{", "[")

        # Replace } with ]
        attr_value = attr_value.replace("}", "]")

        return attr_value

    def get_field_or_lang_dict_value(self, field, lang=None):
        if not isinstance(field, dict):
            return field
        else:
            try:
                if lang is not None:
                    return field[lang]
                else:
                    return next(iter(field))
            except KeyError:
                return ""

    def get_custom_annotations(self):
        custom_annotations = {}
        custom_annotations = dict(
            (k, v)
            for k, v in self.get("bind").items()
            if k.startswith(self.OC_CUSTOM_ANNOTATION_PREFIX)
        )
        return custom_annotations

    def check_custom_annotations(self):
        custom_annotations = self.get_custom_annotations()
        if custom_annotations:
            for key in custom_annotations.keys():
                custom_annotation_label = key[len(self.OC_CUSTOM_ANNOTATION_PREFIX) :]
                if custom_annotation_label != "":
                    # custom_annotation_label should only contains aplhanumeric, underscore, and hypens chars
                    if not bool(re.match(r"^[A-Za-z0-9_-]+$", custom_annotation_label)):
                        msg = "Custom annotation labels can only include letters, digits, underscores, and hyphens."
                        raise PyXFormError(msg)
                    if not bool(re.match(r"^[A-Za-z0-9]$", custom_annotation_label[0])):
                        msg = (
                            "Custom annotation labels must start with a letter or digit."
                        )
                        raise PyXFormError(msg)

    def get_annotated_label(self, lang=None):
        survey = self.get_root()

        if not survey.is_annotated_form():
            self.check_custom_annotations()
            return self.get_field_or_lang_dict_value(self.label, lang)
        else:
            is_choices = self.parent.type in [
                constants.SELECT_ONE,
                constants.SELECT_ALL_THAT_APPLY,
            ]
            is_select_one_from_file = False
            annotated_value_styles = {
                "type": "color: black",
                "name": "color: orangered",
                "itemgroup": "color: blue",
                "relevant": "color: green",
                "required": "color: red",
                "required_type": "color: cornflowerblue",
                "constraint": "color: magenta",
                "constraint_type": "color: darkolivegreen",
                "default": "color: deepskyblue",
                "choice_filter": "color: dodgerblue",
                "calculation": "color: maroon",
                "trigger": "color: darkgreen",
                "readonly": "color: chocolate",
                "image": "color: darkviolet",
                "video": "color: darkviolet",
                "audio": "color: darkviolet",
                "repeat_count": "color: lime",
                "external": "color: indigo",
                "contactdata": "color: tomato",
                "identifier": "color: tomato",
                "custom": "color: black",
            }

            # Item label
            annotated_label = self.get_field_or_lang_dict_value(self.label, lang)
            annotated_label = self.annotated_value_processing(annotated_label, "label")

            # if item is choices
            if is_choices and hasattr(self, "label") and hasattr(self, "name"):
                choice_label = self.get_field_or_lang_dict_value(
                    getattr(self, "label"), lang
                )
                annotated_label = "{} [{}]".format(choice_label, getattr(self, "name"))
                annotated_label = self.annotated_value_processing(
                    annotated_label, "choices"
                )
            else:
                # Non-Choice fields
                for idx, annotated_field in enumerate(survey.annotated_fields):
                    if not hasattr(self, annotated_field) and annotated_field not in [
                        "itemgroup",
                        "relevant",
                        "required",
                        "required_type",
                        "constraint",
                        "constraint_type",
                        "calculation",
                        "readonly",
                        "image",
                        "video",
                        "audio",
                        "repeat_count",
                        "external",
                        "contactdata",
                        "identifier",
                        "custom",
                    ]:
                        continue

                    attr_label = annotated_field.title()
                    attr_value = ""
                    attr_style = ""
                    field_annotations = {}
                    custom_annotations = {}

                    if hasattr(self, annotated_field):
                        attr_value = getattr(self, annotated_field)

                    # Annotated field handling
                    if annotated_field == "type":
                        if attr_value in [
                            constants.SELECT_ONE,
                            constants.SELECT_ALL_THAT_APPLY,
                        ]:
                            if attr_value == constants.SELECT_ONE:
                                attr_value = attr_value.replace(" ", "_")  # select_one
                            elif attr_value == constants.SELECT_ALL_THAT_APPLY:
                                attr_value = "select_multiple"

                            if (
                                hasattr(self, "list_name")
                                and getattr(self, "list_name") != ""
                            ):
                                attr_value += " " + getattr(self, "list_name")
                            elif (
                                hasattr(self, "itemset")
                                and getattr(self, "itemset") != ""
                            ):
                                is_select_one_from_file = True
                                attr_value += "_from_file " + getattr(self, "itemset")
                        elif attr_value == "photo":
                            attr_value = "image"
                    elif annotated_field == "itemgroup":
                        attr_value = self.get("bind", {}).get("oc:itemgroup", "")
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_ITEMGROUP
                    elif annotated_field == "relevant":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("bind", {}).get("relevant", ""), lang
                        )
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_RELEVANT
                    elif annotated_field == "required":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("bind", {}).get("required", ""), lang
                        )
                    elif annotated_field == "required_type":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("bind", {}).get("oc:required-type", ""), lang
                        )
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_REQUIRED_TYPE
                    elif annotated_field == "constraint":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("bind", {}).get("constraint", ""), lang
                        )
                    elif annotated_field == "constraint_type":
                        attr_value = self.get("bind", {}).get("oc:constraint-type", "")
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_CONSTRAINT_TYPE
                    elif annotated_field == "calculation":
                        attr_value = self.get("bind", {}).get("calculate", "")
                    elif annotated_field == "readonly":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("bind", {}).get("readonly", ""), lang
                        )
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_READONLY
                    elif annotated_field == "image":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("media", {}).get("image", ""), lang
                        )
                    elif annotated_field == "video":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("media", {}).get("video", ""), lang
                        )
                    elif annotated_field == "audio":
                        attr_value = self.get_field_or_lang_dict_value(
                            self.get("media", {}).get("audio", ""), lang
                        )
                    elif annotated_field == "repeat_count" and self.type == "repeat":
                        # Repeat count could be in the top level children or in a group
                        repeat_count_name = f"{self.name}_count"

                        # Search in top-level children
                        repeat_count_model = next(
                            (
                                child
                                for child in survey.children
                                if child["name"] == repeat_count_name
                            ),
                            None,
                        )

                        # If not found, search in group children
                        if repeat_count_model is None:
                            for survey_child in survey.children:
                                if survey_child["type"] == "group":
                                    repeat_count_model = next(
                                        (
                                            child
                                            for child in survey_child.children
                                            if child["name"] == repeat_count_name
                                        ),
                                        None,
                                    )
                                    if repeat_count_model:
                                        break

                        if repeat_count_model:
                            attr_value = repeat_count_model.get("bind", {}).get(
                                "calculate", ""
                            )
                            if attr_value:
                                attr_label = constants.ANNOTATE_REPEAT_COUNT
                    elif annotated_field == "external":
                        attr_value = self.get("bind", {}).get("oc:external", "")
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_EXTERNAL
                    elif annotated_field == "contactdata":
                        attr_value = self.get("instance", {}).get("oc:contactdata", "")
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_CONTACTDATA
                    elif annotated_field == "choice_filter":
                        if attr_value != "":
                            attr_label = constants.ANNOTATE_CHOICE_FILTER
                    elif annotated_field == "identifier":
                        attr_value = self.get("instance", {}).get("oc:identifier", "")
                    elif annotated_field == "custom":
                        # Custom annotations handling
                        self.check_custom_annotations()
                        custom_annotations = self.get_custom_annotations()
                        if custom_annotations:
                            for key in custom_annotations.keys():
                                attr_value = custom_annotations[key]
                                attr_label = key[len(self.OC_CUSTOM_ANNOTATION_PREFIX) :]

                                # Change _ with space in custom annotation label
                                if attr_label != "" and "_" in attr_label:
                                    attr_label = attr_label.replace("_", " ").strip()

                                field_annotations[attr_label] = attr_value

                    # Annotated value style
                    if annotated_field in annotated_value_styles.keys():
                        attr_style = annotated_value_styles[annotated_field]

                    if len(custom_annotations) == 0:
                        field_annotations[attr_label] = attr_value

                    # Annotated value assignment
                    for label, value in field_annotations.items():
                        if label != "" and value != "":
                            value = "".join(value.splitlines())
                            value = self.annotated_value_processing(
                                value, annotated_field
                            )
                            annotated_value = "{}: {}".format(label, value)
                            attributes = {}
                            if attr_style != "":
                                attributes["style"] = attr_style

                            annotated_label_value = " [{}]".format(annotated_value)

                            # Annotation(s) should be displayed in newline after item's Label
                            if idx == 0:
                                annotated_label += "\n"

                            if attr_style == "":
                                annotated_label += annotated_label_value
                            else:
                                annotated_label += '<span style="{}">{}</span>'.format(
                                    attr_style, annotated_label_value
                                )

            if is_select_one_from_file:
                annotated_label += "<br>"
                annotated_label += constants.ANNOTATE_SELECT_ONE_FROM_FILE_MESSAGE

            return annotated_label

    # XML generating functions, these probably need to be moved around.
    def xml_label(self):
        if self.needs_itext_ref():
            # If there is a dictionary label, or non-empty media dict,
            # then we need to make a label with an itext ref
            ref = "jr:itext('%s')" % self._translation_path("label")
            return node("label", ref=ref)
        else:
            survey = self.get_root()
            output_label = self.label

            # Annotate fields in survey.annotated_fields
            annotated_label = self.get_annotated_label()
            if annotated_label != output_label:
                output_label = annotated_label

            label, output_inserted = survey.insert_output_values(output_label, self)
            return node("label", label, toParseString=output_inserted)

    def xml_hint(self):
        if isinstance(self.hint, dict) or self.guidance_hint:
            path = self._translation_path("hint")
            return node("hint", ref="jr:itext('%s')" % path)
        else:
            hint, output_inserted = self.get_root().insert_output_values(self.hint, self)
            return node("hint", hint, toParseString=output_inserted)

    def xml_label_and_hint(self) -> "List[DetachableElement]":
        """
        Return a list containing one node for the label and if there
        is a hint one node for the hint.
        """
        result = []
        label_appended = False
        if (
            self.label
            or self.media
            or (self.get_root().is_annotated_form() and self.type == "calculate")
        ):
            result.append(self.xml_label())
            label_appended = True

        if self.hint or self.guidance_hint:
            if not label_appended:
                result.append(self.xml_label())
            result.append(self.xml_hint())

        msg = "The survey element named '%s' " "has no label or hint." % self.name
        if len(result) == 0 and not self.get_root().is_annotated_form():
            raise PyXFormError(msg)

        # Guidance hint alone is not OK since they may be hidden by default.
        if not any((self.label, self.media, self.hint)) and self.guidance_hint:
            raise PyXFormError(msg)

        # big-image must combine with image
        if "image" not in self.media and "big-image" in self.media:
            raise PyXFormError(
                "To use big-image, you must also specify an image for the survey element named {self.name}."
            )

        return result

    def xml_bindings(self):
        """
        Return the binding(s) for this survey element.
        """
        survey = self.get_root()
        bind_dict = self.bind.copy()
        if self.get("flat"):
            # Don't generate bind element for flat groups.
            return None
        if bind_dict:
            # the expression goes in a setvalue action
            if self.trigger and "calculate" in self.bind:
                del bind_dict["calculate"]

            # Annotated form bind handling
            if survey.is_annotated_form():
                # Do not include "relevant" binding in annotated form
                if "relevant" in survey.annotated_fields and "relevant" in self.bind:
                    return None
                elif (
                    "calculation" in survey.annotated_fields and "calculate" in self.bind
                ):
                    bind_dict["calculate"] = "string('')"

            for k, v in bind_dict.items():
                # I think all the binding conversions should be happening on
                # the xls2json side.
                if (
                    hashable(v)
                    and v in self.BINDING_CONVERSIONS
                    and k in self.CONVERTIBLE_BIND_ATTRIBUTES
                ):
                    v = self.BINDING_CONVERSIONS[v]
                if k == "jr:constraintMsg" and (
                    type(v) is dict or re.search(BRACKETED_TAG_REGEX, v)
                ):
                    v = "jr:itext('%s')" % self._translation_path("jr:constraintMsg")
                if k == "jr:requiredMsg" and (
                    type(v) is dict or re.search(BRACKETED_TAG_REGEX, v)
                ):
                    v = "jr:itext('%s')" % self._translation_path("jr:requiredMsg")
                if k == "jr:noAppErrorString" and type(v) is dict:
                    v = "jr:itext('%s')" % self._translation_path("jr:noAppErrorString")
                bind_dict[k] = survey.insert_xpaths(v, context=self)
            return [node("bind", nodeset=self.get_xpath(), **bind_dict)]
        return None

    def xml_descendent_bindings(self):
        """
        Return a list of bindings for this node and all its descendants.
        """
        result = []
        for e in self.iter_descendants():
            xml_bindings = e.xml_bindings()
            if xml_bindings is not None:
                result.extend(xml_bindings)

            # dynamic defaults for repeats go in the body. All other dynamic defaults (setvalue actions) go in the model
            if (
                len(
                    [
                        ancestor
                        for ancestor in e.get_lineage()
                        if ancestor.type == "repeat"
                    ]
                )
                == 0
            ):
                dynamic_default = e.get_setvalue_node_for_dynamic_default()
                if dynamic_default:
                    result.append(dynamic_default)
        return result

    def xml_control(self):
        """
        The control depends on what type of question we're asking, it
        doesn't make sense to implement here in the base class.
        """
        raise NotImplementedError("Control not implemented")

    def xml_action(self):
        """
        Return the action for this survey element.
        """
        if self.action:
            action_dict = self.action.copy()
            if action_dict:
                name = action_dict["name"]
                del action_dict["name"]
                return node(name, ref=self.get_xpath(), **action_dict)

        return None

    def xml_actions(self):
        """
        Return a list of actions for this node and all its descendants.
        """
        result = []
        for e in self.iter_descendants():
            xml_action = e.xml_action()
            if xml_action is not None:
                result.append(xml_action)
        return result


def hashable(v):
    """Determine whether `v` can be hashed."""
    try:
        hash(v)
    except TypeError:
        return False
    return True
