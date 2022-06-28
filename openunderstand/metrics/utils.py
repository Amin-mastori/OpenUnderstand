import os
from antlr4 import *
from gen.javaLabeled.JavaLexer import JavaLexer
from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled


def make_scope_method(ctx):
    prefixes = get_method_prefixes(ctx)
    kind_name = get_kind_name(prefixes, kind="Method")
    method_name = ctx.children[1]
    return_type = ctx.children[0].getText()
    access_type = ctx.parentCtx.parentCtx.children[0].getText()
    static_type = ''
    if len(ctx.parentCtx.parentCtx.children) > 1:
        if ctx.parentCtx.parentCtx.children[1].getText() == 'static':
            static_type = ctx.parentCtx.parentCtx.children[1].getText()
    return {
        'kind_name': kind_name,
        'method_name': method_name,
        'return_type': return_type,
        'access_type': access_type,
        'static_type': static_type
    }


def make_scope_interface(ctx):
    prefixes = get_class_prefixes(ctx, "InterfaceDeclarationContext")
    kind_name = get_kind_name(prefixes, kind="Class")
    class_name = ctx.children[1]
    return_type = ctx.children[0].getText()
    access_type = ctx.parentCtx.parentCtx.children[0].getText()
    if ctx.parentCtx.parentCtx.children[1].getText() == 'static':
        static_type = ctx.parentCtx.parentCtx.children[1].getText()
    else:
        static_type = ''
    return {
        'kind_name': kind_name,
        'method_name': class_name,
        'return_type': return_type,
        'access_type': access_type,
        'static_type': static_type
    }


def make_scope_annotation(ctx):
    prefixes = get_class_prefixes(ctx, "AnnotationTypeDeclarationContext")
    kind_name = get_kind_name(prefixes, kind="Class")
    class_name = ctx.children[1]
    return_type = ctx.children[0].getText()
    access_type = ctx.parentCtx.parentCtx.children[0].getText()
    if ctx.parentCtx.parentCtx.children[1].getText() == 'static':
        static_type = ctx.parentCtx.parentCtx.children[1].getText()
    else:
        static_type = ''
    return {
        'kind_name': kind_name,
        'method_name': class_name,
        'return_type': return_type,
        'access_type': access_type,
        'static_type': static_type
    }


def find_scope(ctx):
    scope = []
    if str(ctx.children[0]) == 'package':
        return [{
            'kind_name': 'Java Package',
            'method_name': ctx.children[1].getText(),
            'return_type': '',
            'access_type': '',
            'static_type': ''
        }]
    scope_ctx = search_scope(ctx, ["ClassDeclarationContext", "MethodDeclarationContext",
                                   "InterfaceDeclarationContext", "AnnotationTypeDeclarationContext"])
    for item in scope_ctx:
        if type(item).__name__ == "ClassDeclarationContext":
            scope.append(make_scope_class(item))
        elif type(item).__name__ == "MethodDeclarationContext":
            scope.append(make_scope_method(item))
        elif type(item).__name__ == "InterfaceDeclarationContext":
            scope.append(make_scope_interface(item))
        elif type(item).__name__ == "AnnotationTypeDeclarationContext":
            scope.append(make_scope_annotation(item))
    return scope


class Project:
    def __init__(self, project_dir, project_name=None):
        self.project_dir = project_dir
        self.project_name = project_name
        self.files = []

    def get_java_files(self):
        for dir_path, _, file_names in os.walk(self.project_dir):
            for file in file_names:
                if '.java' in str(file):
                    path = os.path.join(dir_path, file)
                    path = path.replace("/", "\\")
                    path = os.path.abspath(path)
                    self.files.append((file, path))


def get_project_info(index, ref_name=None):
    project_names = [
        'calculator_app',
        'JSON',
        'testing_legacy_code',
        'jhotdraw-develop',
        'xerces2j',
        'jvlt-1.3.2',
        'jfreechart',
        'ganttproject',
        '105_freemind',
        'custom'
    ]
    project_name = project_names[index]
    db_path = f"../../../databases/{ref_name}/{project_name}"
    if ref_name == "origin":
        db_path = db_path + ".udb"
    else:
        db_path = db_path + ".oudb"
    project_path = f"../../../benchmarks/{project_name}"

    db_path = os.path.abspath(db_path)
    project_path = os.path.abspath(project_path)

    return {
        'PROJECT_NAME': project_name,
        'DB_PATH': db_path,
        'PROJECT_PATH': project_path,
    }


def get_parse_tree(file_path):
    file = FileStream(file_path, encoding="utf-8")
    lexer = JavaLexer(file)
    tokens = CommonTokenStream(lexer)
    parser = JavaParserLabeled(tokens)
    return parser.compilationUnit()


def get_kind_name(prefixes, kind):
    p_static = ""
    p_abstract = ""
    p_generic = ""
    p_type = "Type"
    p_visibility = "Default"
    p_member = "Member"

    if "static" in prefixes:
        p_static = "Static"

    if "generic" in prefixes:
        p_generic = "Generic"

    if "abstract" in prefixes:
        p_abstract = "Abstract"
    elif "final" in prefixes:
        p_abstract = "Final"

    if "private" in prefixes:
        p_visibility = "Private"
    elif "public" in prefixes:
        p_visibility = "Public"
    elif "protected" in prefixes:
        p_visibility = "Protected"

    if kind == "Interface":
        p_member = ""

    if kind == "Method":
        p_type = ""

    s = f"Java {p_static} {p_abstract} {p_generic} {kind} {p_type} {p_visibility} {p_member}"
    s = " ".join(s.split())
    return s


def get_method_prefixes(ctx):
    access_branches = ctx.parentCtx.parentCtx.children
    type_branches = ctx.children
    prefixes = []

    for branch in access_branches:
        if type(branch).__name__ == "ModifierContext":
            prefixes.append(branch.getText())

    for branch in type_branches:
        if type(branch).__name__ == "TypeTypeOrVoidContext":
            prefixes.append(branch.getText())

    return prefixes


def get_class_prefixes(ctx, ctx_type):
    branches = ctx.parentCtx.children
    prefixes = ""
    for branch in branches:
        if type(branch).__name__ == ctx_type:
            break
        prefixes += branch.getText() + " "
    return prefixes


def search_scope(ctx, type_names):
    # Traverse bottom up until reaching a class or method
    scope_list = []
    current = ctx.parentCtx
    while current is not None:
        type_name = type(current).__name__
        if type_name in type_names:
            scope_list.append(current)
        current = current.parentCtx
    return scope_list


def get_parent(parent_file_name, files):
    file_names, file_paths = zip(*files)
    parent_file_index = file_names.index(parent_file_name)
    parent_file_path = file_paths[parent_file_index]
    return parent_file_path


def make_scope_class(ctx):
    prefixes = get_class_prefixes(ctx, "ClassDeclarationContext")
    kind_name = get_kind_name(prefixes, kind="Class")
    class_name = ctx.children[1]
    return_type = ctx.children[0].getText()
    access_type = ctx.parentCtx.parentCtx.children[0].getText()
    if ctx.parentCtx.parentCtx.children[1].getText() == 'static':
        static_type = ctx.parentCtx.parentCtx.children[1].getText()
    else:
        static_type = ''
    return {
        'kind_name': kind_name,
        'method_name': class_name,
        'return_type': return_type,
        'access_type': access_type,
        'static_type': static_type
    }
