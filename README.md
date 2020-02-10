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

Options for AltStructure are specified in the `alt_structure` section at the root of Foliant config file:

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
    - basic:  # <-- this is _chapter tree category_
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

> AltStructure extension introduces a lot of new notions so to make sure we are on the same page, let's agree on some terms. _Chapter tree category_ is a mapping with single key which you add to your chapter list to create hierarchy. `basic:` and `Alternative:` are categories in this example.

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

Next you need to define the structure in `structure` parameter of extension config. It is defined by list of *node types*, or a single string with node types, divided by separators. For example:

```yaml
alt_structure:
    structure:
        - ['topic', 'entity']  # list with two node types
        - 'additional/glossaries'  # single string with two node types and separator /
```

These names of the node types are arbitrary, you can use any words you like except `root` and `subfolder`.

**Step 3**

Open your source md-files and edit their *main meta sections*. Main meta section is a section, defined before the first heading in the document (check [metadata documentation](https://foliant-docs.github.io/docs/cli/meta/) for details). Add a mapping with nodes for this chapter under the key `structure`.

file auth_spec.md
```yaml
---
structure:
    topic: auth  # <-- node type: node name
    entity: spec
---

# Specification for authorization
```

Here `topic` and `entity` are node types, which are part of our structure (step 2). `auth` and `spec` are *node names*. After applying `!alt_structure` tag nodes will be converted into chapter tree categories. Node type defines the level of the category and node name defines the caption of the category.

We've added two nodes to the `structure` field of chapter metadata: `topic: auth` and `entity: spec`. In the structure that we've defined on step 2 the `topic` goes first and `entity` — second. So after applying the tag, this chapter will appear in config like this:

```yaml
- auth:
    - spec:
        - auth_spec.md
```

If we'd stated only `topic` key in metadata, then it would look like this:

```yaml
- auth:
    - auth_spec.md
```

**Step 4**

Now let's fill up registry. We used `spec` and `auth` in our metadata for node names, but these words don't look pretty in the documents. Registry allows us to set verbose captions for node names in config:

```yaml
alt_structure:
    structure:
        - ['topic', 'entity']
        - 'additional/glossaries'
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

### Special node types

In the step 2 of the user guide above we've mentioned that you may choose any node names in the structure except `root` and `subfolder`. These are special note types and here's how you can use them.

**root**

For example, if our structure looks like this:

```yaml
alt_structure:
    structure:
        - ['topic', 'entity']
```
and our chapter's metadata looks like this:

```yaml
---
structure:
    foo: bar
---
```

The node `foo: bar` is not part of the structure, so applying the `!alt_structure` tag it will just be ignored (unless `add_unmatched_to_root` is set to `true` in config). But what if you want to add it to the root of your chapter tree?

To do that — add the `root` node to your metadata:

```yaml
---
structure:
    foo: bar
    root: true  # the value of the key `root` is ignored, we use `true` for clarity
---
```

Please note that if you add `root: true` to meta, the chapter will be sent to root of your tree *only* if it wasn't matched by your structure definition.

So in the following example it will still appear under node `auth` and `root: true` will be ignored:

```yaml
---
structure:
    topic: auth
    root: true  # ignored
---
```

**subfolder**

By defining `subfolder` node in chapter's metadata you can manually add another chapter tree category to any chapter.

For example:

file auth_spec.md
```yaml
---
structure:
    topic: auth
    entity: spec
    subfolder: Main specifications
---
```

After applying tag the new structure will look like this:

```yaml
- auth:
    - spec:
        - Main specifications:
            - auth_spec.md
```

### Using preprocessor

By default the `!alt_structure` tag only affects the `chapters` section of your foliant.yml. This may lead to situation when the same file is mentioned several times in the `chapters` section. While most backends are fine with that — they will just publish the file two times, [MkDocs](https://foliant-docs.github.io/docs/backends/mkdocs/) does not handle this situation well.

That's where you will need to add the preprocessor `alt_structure` to your preprocessors list. Preprocessor creates a subfolder in the working_dir and copies the entier working_dir contents into it. Then it inserts the subfolder name into the beginning of all chapters paths in the alternative structure.

> **Important:** It is recommended to add this preprocessor to the end of the preprocessors list.

```yaml

preprocessors:
    ...
    alt_structure:
        create_subfolders: true
```

Note, that the parameter `create_subfolders` is not necessary, it is `true` by default. But we recommend to state it anyway for clarity.

After applying the tag, your new structure will now look like this:

```yaml
- Authentication and Authorization:
    - Specifications:
        - alt1/auth_spec.md
```

The contents of the working_dir were copied into a subdir `alt1`, and new structure refers to the files in this subdir.