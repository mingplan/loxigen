# Copyright 2013, Big Switch Networks, Inc.
#
# LoxiGen is licensed under the Eclipse Public License, version 1.0 (EPL), with
# the following special exception:
#
# LOXI Exception
#
# As a special exception to the terms of the EPL, you may distribute libraries
# generated by LoxiGen (LoxiGen Libraries) under the terms of your choice, provided
# that copyright and licensing notices generated by LoxiGen are not altered or removed
# from the LoxiGen Libraries and the notice provided below is (i) included in
# the LoxiGen Libraries, if distributed in source code form and (ii) included in any
# documentation for the LoxiGen Libraries, if distributed in binary form.
#
# Notice: "Copyright 2013, Big Switch Networks, Inc. This library was generated by the LoxiGen Compiler."
#
# You may not use this file except in compliance with the EPL or LOXI Exception. You may obtain
# a copy of the EPL at:
#
# http://www.eclipse.org/legal/epl-v10.html
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# EPL for the specific language governing permissions and limitations
# under the EPL.

"""
@brief Dump function generation

Generates dump function files.

"""

import sys
import of_g
import c_gen.match as match
import c_gen.flags as flags
from generic_utils import *
import c_gen.type_maps as type_maps
import c_gen.loxi_utils_legacy as loxi_utils
import c_gen.identifiers as identifiers
from c_test_gen import var_name_map

def gen_obj_dump_h(out, name):
    loxi_utils.gen_c_copy_license(out)
    out.write("""
/**
 *
 * AUTOMATICALLY GENERATED FILE.  Edits will be lost on regen.
 *
 * Header file for object dumping.
 */

/**
 * Dump  object declarations
 *
 * Routines that emit a dump of each object.
 *
 */

#if !defined(_LOCI_OBJ_DUMP_H_)
#define _LOCI_OBJ_DUMP_H_

#include <loci/loci.h>
#include <stdio.h>

/* g++ requires this to pick up PRI, etc.
 * See  http://gcc.gnu.org/ml/gcc-help/2006-10/msg00223.html
 */
#if !defined(__STDC_FORMAT_MACROS)
#define __STDC_FORMAT_MACROS
#endif
#include <inttypes.h>


/**
 * Dump any OF object.
 */
int of_object_dump(loci_writer_f writer, void* cookie, of_object_t* obj);






""")

    type_to_emitter = dict(

        )
    for version in of_g.of_version_range:
        for cls in of_g.standard_class_order:
            if not loxi_utils.class_in_version(cls, version):
                continue
            if cls in type_maps.inheritance_map:
                continue
            out.write("""\
int %(cls)s_%(ver_name)s_dump(loci_writer_f writer, void* cookie, %(cls)s_t *obj);
""" % dict(cls=cls, ver_name=loxi_utils.version_to_name(version)))

    out.write("""
#endif /* _LOCI_OBJ_DUMP_H_ */
""")

def gen_obj_dump_c(out, name):
    loxi_utils.gen_c_copy_license(out)
    out.write("""
/**
 *
 * AUTOMATICALLY GENERATED FILE.  Edits will be lost on regen.
 *
 * Source file for object dumping.
 *
 */

#define DISABLE_WARN_UNUSED_RESULT
#include <loci/loci.h>
#include <loci/loci_dump.h>
#include <loci/loci_obj_dump.h>

static int
unknown_dump(loci_writer_f writer, void* cookie, of_object_t *obj)
{
    return writer(cookie, "Unable to print object of type %d, version %d\\n",
                         obj->object_id, obj->version);
}
""")

    for version in of_g.of_version_range:
        ver_name = loxi_utils.version_to_name(version)
        for cls in of_g.standard_class_order:
            if not loxi_utils.class_in_version(cls, version):
                continue
            if cls in type_maps.inheritance_map:
                continue
            out.write("""
int
%(cls)s_%(ver_name)s_dump(loci_writer_f writer, void* cookie, %(cls)s_t *obj)
{
    int out = 0;
""" % dict(cls=cls, ver_name=ver_name))

            members, member_types = loxi_utils.all_member_types_get(cls, version)
            for m_type in member_types:
                if loxi_utils.type_is_scalar(m_type) or m_type in \
                        ["of_match_t", "of_octets_t"]:
                    # Declare instance of these
                    out.write("    %s %s;\n" % (m_type, var_name_map(m_type)))
                else:
                    out.write("""
    %(m_type)s %(v_name)s;
"""  % dict(m_type=m_type, v_name=var_name_map(m_type)))
                    if loxi_utils.class_is_list(m_type):
                        base_type = loxi_utils.list_to_entry_type(m_type)
                        out.write("    %s elt;\n    int rv;\n" % base_type)
            out.write("""
    out += writer(cookie, "Object of type %(cls)s\\n");
""" % dict(cls=cls))
            for member in members:
                m_type = member["m_type"]
                m_name = member["name"]
                emitter = "LOCI_DUMP_" + loxi_utils.type_to_short_name(m_type)
                if loxi_utils.skip_member_name(m_name):
                    continue
                if (loxi_utils.type_is_scalar(m_type) or
                    m_type in ["of_match_t", "of_octets_t"]):
                    out.write("""
    %(cls)s_%(m_name)s_get(obj, &%(v_name)s);
    out += writer(cookie, "  %(m_name)s (%(m_type)s):  ");
    out += %(emitter)s(writer, cookie, %(v_name)s);
    out += writer(cookie, "\\n");
""" % dict(cls=cls, m_name=m_name, m_type=m_type,
           v_name=var_name_map(m_type), emitter=emitter))
                elif loxi_utils.class_is_list(m_type):
                    sub_cls = m_type[:-2] # Trim _t
                    elt_type = loxi_utils.list_to_entry_type(m_type)
                    out.write("""
    out += writer(cookie, "List of %(elt_type)s\\n");
    %(cls)s_%(m_name)s_bind(obj, &%(v_name)s);
    %(u_type)s_ITER(&%(v_name)s, &elt, rv) {
        of_object_dump(writer, cookie, (of_object_t *)&elt);
    }
""" % dict(sub_cls=sub_cls, u_type=sub_cls.upper(), v_name=var_name_map(m_type),
           elt_type=elt_type, cls=cls, m_name=m_name, m_type=m_type))
                else:
                    sub_cls = m_type[:-2] # Trim _t
                    out.write("""
    %(cls)s_%(m_name)s_bind(obj, &%(v_name)s);
    out += %(sub_cls)s_%(ver_name)s_dump(writer, cookie, &%(v_name)s);
""" % dict(cls=cls, sub_cls=sub_cls, m_name=m_name,
           v_name=var_name_map(m_type), ver_name=ver_name))

            out.write("""
    return out;
}
""")
    out.write("""
/**
 * Log a match entry
 */
int
loci_dump_match(loci_writer_f writer, void* cookie, of_match_t *match)
{
    int out = 0;

    out += writer(cookie, "Match obj, version %d.\\n", match->version);
""")

    for key, entry in match.of_match_members.items():
        m_type = entry["m_type"]
        emitter = "LOCI_DUMP_" + loxi_utils.type_to_short_name(m_type)
        out.write("""
    if (OF_MATCH_MASK_%(ku)s_ACTIVE_TEST(match)) {
        out += writer(cookie, "  %(key)s (%(m_type)s) active: Value ");
        out += %(emitter)s(writer, cookie, match->fields.%(key)s);
        out += writer(cookie, "\\n    Mask ");
        out += %(emitter)s(writer, cookie, match->masks.%(key)s);
        out += writer(cookie, "\\n");
    }
""" % dict(key=key, ku=key.upper(), emitter=emitter, m_type=m_type))

    out.write("""
    return out;
}
""")

    # Generate big table indexed by version and object
    for version in of_g.of_version_range:
        out.write("""
static const loci_obj_dump_f dump_funs_v%(version)s[OF_OBJECT_COUNT] = {
""" % dict(version=version))
        out.write("    unknown_dump, /* of_object, not a valid specific type */\n")
        for j, cls in enumerate(of_g.all_class_order):
            comma = ""
            if j < len(of_g.all_class_order) - 1: # Avoid ultimate comma
                comma = ","

            if (not loxi_utils.class_in_version(cls, version) or
                    cls in type_maps.inheritance_map):
                out.write("    unknown_dump%s\n" % comma);
            else:
                out.write("    %s_%s_dump%s\n" %
                          (cls, loxi_utils.version_to_name(version), comma))
        out.write("};\n\n")

    out.write("""
static const loci_obj_dump_f *const dump_funs[5] = {
    NULL,
    dump_funs_v1,
    dump_funs_v2,
    dump_funs_v3,
    dump_funs_v4
};

int
of_object_dump(loci_writer_f writer, void* cookie, of_object_t *obj)
{
    if ((obj->object_id > 0) && (obj->object_id < OF_OBJECT_COUNT)) {
        if (((obj)->version > 0) && ((obj)->version <= OF_VERSION_1_3)) {
            /* @fixme VERSION */
            return dump_funs[obj->version][obj->object_id](writer, cookie, (of_object_t *)obj);
        } else {
            return writer(cookie, "Bad version %d\\n", obj->version);
        }
    }
    return writer(cookie, "Bad object id %d\\n", obj->object_id);
}
""")

