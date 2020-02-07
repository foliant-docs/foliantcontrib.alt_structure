[![](https://img.shields.io/pypi/v/foliantcontrib.alt_structure.svg)](https://pypi.org/project/foliantcontrib.alt_structure/)

# AltStructure Extension

AltStructure is a config extension for Foliant to generate alternative chapter structure based on metadata.

It adds an `alt_structure` preprocessor and resolves `!alt_structure` YAML tags in the project config.

## Installation

```bash
$ pip install foliantcontrib.alt_structure
```

## Configuration

**Config extension**

Options for AltStructure are specified in the `alt_structure` section at the root root of Foliant config file:

```yaml
alt_structure:
    structure:
        - "topic/entity"
        - "additional"
    sep: '/'
    add_unmatched_to_root: false
    registry:
        topic:
            auth: Аутентификация и авторизация
            weather: Погода
        entity:
            test_case: Тест кейсы
            spec: Спецификации
```

`structure`
:   *(required)* List of structure strings (or lists), each of them representing a branch in chapters structure.

`sep`
:   separator for structure strings (ignored for structure lists). Deafault: `/`

`add_unmatched_to_root`
:   if `true`, all chapters that weren't matched to structure in metadata will be added to root of the chapter tree. If `false` — they will be ignored. Default: `false`

`registry`
:   A dictionary which defines aliases for chapter tree categories.

**Preprocessor**

Preprocessor has just one option:

```yaml
preprocessors:
    - alt_structure:
        create_subfolders: true
```

`create_subfolders`
:   If `true`, preprocessor will create a full copy of the working_dir and add it to the beginning of all filepaths in the generated structure. If `false` — preprocessor doesn't do anything. Default: `true`

## Usage

**Step 1**

Add `!alt_structure` tag to your chapters in the place where you expect new structure to be generated. It accepts one argument: list of chapters, which will be scanned.

```yaml
chapters:
    - basic:
        - auth/auth.md
        - index.md
        - auth/test_auth.md
        - auth/test_auth_aux.md
        - weather.md
        - glossary.md
        - auth/spec_auth.md
        - test_weather.md
    - Alternative: !alt_structure
        - auth/auth.md
        - index.md
        - auth/test_auth.md
        - auth/test_auth_aux.md
        - weather.md
        - glossary.md
        - auth/spec_auth.md
        - test_weather.md
```

You can also utilize YAML anchors and aliases, but in this case, because of language limitation you need to supply alias inside a list. Let's use it to get the same result as the above, but in a more compact way:

```yaml
chapters:
    - basic: &basic
        - auth/auth.md
        - index.md
        - auth/test_auth.md
        - auth/test_auth_aux.md
        - weather.md
        - glossary.md
        - auth/spec_auth.md
        - test_weather.md
    - Alternative: !alt_structure [*basic]
```

**Step 2**

Next you need to define the structure in `structure` parameter of extension config. It is defined by list of categories, or a string with separators. For example:

```yaml
alt_structure:
    structure:
        - 'topic/entity'
        - 'additional'
```

Here `topic` we may mean different processes which you are describing in the documents, for example, "authorization", "purchases" or "profile editing". `entity` may be the type of the document, for example, "test case" or "specification". We also add an `additional` category for some other documents.

These names are arbitrary, you can use any words you like except `root` and `subfolder`.

**Step 3**

After that, open your source md-files and edit their *main meta sections*. Main meta section is a section, defined before the first heading in the document (check [metadata documentation](https://foliant-docs.github.io/docs/cli/meta/)).

file auth_spec.md
```yaml
---
structure:
    topic: auth
    entity: spec
---

# Specification for authorization
```

We've added a field `structure` to the metadata and defined two subfields in it: `topic` and `entity`. These keys should be part of your structure, which we defined on step 2.

This chapter will be added to the new structure like this:

```yaml
- auth:
    - spec:
        - auth_spec.md
```

If we stated only `topic` key in metadata:

file auth_spec.md
```yaml
---
structure:
    topic: auth
---
```

Then the new structure would be:

```yaml
- auth:
    - auth_spec.md
```

**Step 4**

Now let's fill up registry. We used `spec` and `auth` in our metadata for categorizing our articles, but these words don't look pretty in the documents. Registry allows us to set verbose names for these categories in config:

```yaml
alt_structure:
    structure:
        - 'topic/entity'
        - 'additional'
    registry:
        topic:
            auth: Authentication and Authorization
        entity:
            spec: Specifications
```

With such registry now our new structure will look like this:

```yaml
- Authentication and Authorization:
    - Specifications:
        - auth_spec.md
```

### Using preprocessor

By default the `!alt_structure` tag just adds a new chapter structure to config. This may lead to situation when the same file is mentioned several times in the `chapters` section (like in our example). While most backends are fine with that — they will just publish the file two times, but [MkDocs](https://foliant-docs.github.io/docs/backends/mkdocs/) does not handle this situation well.

That's where you will need to add the preprocessor `alt_structure` to your preprocessors list. Preprocessor creates a subfolder in the working_dir and copies the entier working_dir contents into it. Then it insets the subfolder name into the beginning of all chapters paths in the alternative structure.

It is recommended to add this preprocessor to the end of the preprocessors list.

```yaml

preprocessors:
    ...
    alt_structure:
        create_subfolders: true
```

> Note, that the parameter `create_subfolders` is not necessary, it is `true` by default. But we recommend to state it anyway for clarity.

After applying the tag, your new structure will now look like this:

```yaml
- Authentication and Authorization:
    - Specifications:
        - alt1/auth_spec.md
```

The contents of the working_dir were copied into a subdir `alt1`, and new structure refers to the files in this subdir.