import xmltodict
from collections import defaultdict
import sys
import os
import traceback
import argparse

'''
convert a S-100 FC xml to an html human readable
Still bug with associations, anchorage area for example we don't have the name of the feat associated
Check if it's in the xml
'''

def test_coherence_attr (lower, nil, infinite, val):
    """
    teste la cohérence des cardinalités
    si lower = 0 alors upper ppeut etre nul
    si val !=0 alors upper ne peut pas etre infini ni nul
    si upper = 0, lower != 1

    :param lower:
    :param nil:
    :param infinite:
    :param val:
    :return:
    """
    pass
    #a implementer pour ameliorer

def build_alpha_index(items, key):
    alpha_index = defaultdict(list)
    for item in items:
        name = item[key]
        if name:
            first_letter = name[0].upper()
            #print("lettre et nom", first_letter,name)
            alpha_index[first_letter].append(item)
    return dict(sorted(alpha_index.items()))

def extr_upper (upper):
    """
    extrait les information de cardinalité haute d'un attri
    :param upper: dictionnaire upper venant de la cardinalité haute de l'attribut
    :return: un dictionnaire
    """
    #print(upper)
    if isinstance(upper,str):
        peut_val = upper
        peut_infini= ''
        peut_vide=''
    elif isinstance(upper,dict):
        try:
            peut_vide = upper['@xsi:nil']
        except:
            peut_vide= ''
        try:
            peut_infini = upper['@infinite']
        except:
            peut_infini = ''
        try:
            peut_val = upper['#text']
        except:
            peut_val = '*'
    else:
        print("pb avec le format de upper de l'objet")

    vals = {"vide" : peut_vide,
            "infini" : peut_infini,
            "val" : peut_val}
    #print(vals)
    return vals

def extr_attr_from_feat (attributs):
    """
    extraire les attribut d'un objet dans le xml FC, retourne un dictionnaire simplifié
    :param attributs: liste (ou pas) des attributs spécifiques à un objet
    :return: liste dictionnaire des attributs
    """
    attribut_ret = []
    if attributs is not None:
        if isinstance(attributs, list):
            for i in attributs:
                lower = i['S100FC:multiplicity']['S100Base:lower']
                attribut_name = i['S100FC:attribute']['@ref']
                #print(i,i['S100FC:multiplicity']['S100Base:upper'])
                vals = extr_upper(i['S100FC:multiplicity']['S100Base:upper'])
                permitted_values = i.get('S100FC:permittedValues')
                #print('valeurs permises : ',permitted_values)
                if permitted_values is not None:
                    permitted_values["permitted_values"] = permitted_values.pop('S100FC:value')
                attr = {'attribut_name' : attribut_name,
                        'lower' : lower,
                        'upper' : vals,
                        'permitted_values' : permitted_values
                        }
                attribut_ret.append(attr)
        else:
            lower = attributs['S100FC:multiplicity']['S100Base:lower']
            attribut_name = attributs['S100FC:attribute']['@ref']
            vals = extr_upper(attributs['S100FC:multiplicity']['S100Base:upper'])
            permitted_values = attributs.get('S100FC:permittedValues')
            if permitted_values is not None:
                permitted_values["permitted_values"] = permitted_values.pop('S100FC:value')
            attr = {'attribut_name': attribut_name,
                    'lower': lower,
                    'upper': vals,
                    'permitted_values' : permitted_values
                    }

            attribut_ret.append(attr)

    return attribut_ret

def extr_features_infos(data_dict,type):
    """

    :param data_dict:
    :param type: soit 'features', soit 'informations'
    :return:
    """
    liste_obj = []

    if type == 'features':
        try:
            liste_FT = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_FeatureTypes']['S100FC:S100_FC_FeatureType']
        except:
            print('\tNo features found in this standard, check the FC xml file')
            liste_FT = []
    elif type == 'informations':
        try:
            liste_FT = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_InformationTypes']['S100FC:S100_FC_InformationType']
        except:
            print('\tNo information type found in this standard')
            liste_FT = []
    else:
        raise ValueError("Issue with the object type to extract, check the code")

    if isinstance(liste_FT,dict):
        #print("c est un dictionnaire, converison en liste")
        liste_FT = [liste_FT]
    # boucle sur la liste des features
    for i in liste_FT:
        #exraction des propriétés simples de l'objet
        #print(i)

        if not isinstance(i,str):
            try:
                supertype = i['S100FC:superType']
                #print('super =', supertype)
            except:
                supertype = ''
            code = i.get('S100FC:code')
            name = i.get('S100FC:name')
            alias = i.get('S100FC:alias')
            definition = i.get('S100FC:definition')
            featureUseType = i.get('featureUseType')
            primitive = i.get('S100FC:permittedPrimitives')
            # print("Pour l'objet : " + name)
            # print('------------------------')
            attributs = i.get('S100FC:attributeBinding') # peut être None, dict ou dict[]
            attributs = extr_attr_from_feat(attributs)

            try:
                assos_f = i["S100FC:featureBinding"]
                if isinstance(assos_f,dict):
                    assos_f = [assos_f]
            except:
                assos_f = []

            try:
                assos_i = i["S100FC:informationBinding"]
                if isinstance(assos_i,dict):
                    assos_i = [assos_i]
            except:
                assos_i = []

            #print(code, "assos feature:", assos_f, "pour", code)
            #print("assos information:", assos_i, "pour", code)

            mon_objet = {
                "code" : code,
                "name" : name,
                "alias" : alias,
                "definition" : definition,
                "primitive" : primitive,
                "attributes" : attributs,
                "supertype" : supertype,
                "assos_f" : assos_f,
                "assos_i" : assos_i
            }

            liste_obj.append(mon_objet)
    #print(liste_obj)
    return liste_obj

def extr_attributs_simpl (data_dict):
    """

    :param data_dict:
    :return:
    """
    attributs_simples = []
    try:
        liste_att = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_SimpleAttributes']['S100FC:S100_FC_SimpleAttribute']
    except:
        print('No Simple attributes in this standard')
        liste_att = []
    for i in liste_att:
        # print("alias : ", i)
        listed_values = []
        name = i['S100FC:name']
        definition = i['S100FC:definition']
        code = i['S100FC:code']
        type = i['S100FC:valueType']
        if 'S100FC:alias' in i:
            alias = i['S100FC:alias']
        else:
            alias = None

        # print(i)
        if 'S100FC:listedValues' in i :
            if isinstance(i['S100FC:listedValues']['S100FC:listedValue'],list):
                for j in i['S100FC:listedValues']['S100FC:listedValue']:
                    listed_values.append({
                        "label": j['S100FC:label'],
                        "code": j['S100FC:code'],
                        "definition": j['S100FC:definition']
                    })
            else:
                listed_values.append({
                    "label": i['S100FC:listedValues']['S100FC:listedValue']['S100FC:label'],
                    "code": i['S100FC:listedValues']['S100FC:listedValue']['S100FC:code'],
                    "definition": i['S100FC:listedValues']['S100FC:listedValue']['S100FC:definition']
                })

        # print(listed_values)


        attributs_simples.append({
            "name": name,
            "alias": alias,
            "code": code,
            "type": type,
            "definition": definition,
            "listed_values": listed_values,
            # "liste_rel_feat": liste_rel_feat,
            # "liste_rel_attr": liste_rel_attr
        })
    return attributs_simples

def extr_attributs_complex (data_dict):
    """

    :param data_dict:
    :return: dictionnaire des attributs complexes
    """
    attributs_complexes = []

    try:
        liste_ac = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_ComplexAttributes']['S100FC:S100_FC_ComplexAttribute']
    except:
        print("\tNo complex attribute found in this standard")
        liste_ac = []
    for i in liste_ac:
        name = i['S100FC:name']
        definition = i['S100FC:definition']
        code = i['S100FC:code']
        if 'S100FC:alias' in i:
            alias = i['S100FC:alias']
        else:
            alias = None

        attributs = i.get('S100FC:subAttributeBinding') # peut être None, dict ou dict[]

        attributs = extr_attr_from_feat(attributs)


        attributs_complexes.append({
            "name": name,
            "code": code,
            "alias": alias,
            "type": "complex",
            "definition": definition,
            # "liste_rel_feat": liste_rel_feat,
            # "liste_rel_attr" : liste_rel_attr,
            "subattributes": attributs
        })

    return attributs_complexes

def extr_title (data_dict):
    """
    title and general information extraction
    :param data_dict:
    :return:
    """
    try:
        nom = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:name']
    except:
        print("\tIssue with product name")
        nom = ''
    try:
        version = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:versionNumber']
    except:
        print("\tIssue with product version")
        version =''
    try:
        versionDate = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:versionDate']
    except:
        print("\tIssue with product version date")
        versionDate = ''
    try:
        productId = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:productId']
    except:
        print("\tIssue with product id")
        productId = ''


    general = {
        'name': nom,
        'version': version,
        'versionDate': versionDate,
        'productId': productId
    }

    return general

def extr_associations (data_dict):
    """

    :param data_dict:
    :return:
    """

    associations_f = []
    associations_i = []

    try:
        liste_assos_f = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_FeatureAssociations']['S100FC:S100_FC_FeatureAssociation']
    except:
        liste_assos_f = []
    try:
        liste_assos_i = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_InformationAssociations']['S100FC:S100_FC_InformationAssociation']
    except:
        liste_assos_i = []


    #si liste_assos_i n'est pas un tableau
    if isinstance(liste_assos_i,dict):
        l_temp=[]
        l_temp.append(liste_assos_i)
        liste_assos_i = l_temp
    if isinstance(liste_assos_f,dict):
        l_temp=[]
        l_temp.append(liste_assos_f)
        liste_assos_f = l_temp

    #print(f"dict des assos feature : {liste_assos_f}")
    for i in liste_assos_f:
        #print(f"liste des asso : {i}")
        i["type"] = "feature2feature"

    for i in liste_assos_i:
        if not isinstance(i,str):
            i["type"] = "feature2information"
        else:
            print("pb dans asso information")

    if isinstance(liste_assos_i,dict):
        ma_liste = []
        ma_liste.append(liste_assos_i)
        liste_assos_i = ma_liste
    associations = liste_assos_f + liste_assos_i
    associations_index = build_alpha_index(associations,"S100FC:code")

    return associations_index

def extr_asso_feature (data_dict,feature_name):
    """
    pour extraire les association d'une feature class
    :param data_dict: nom du fichier contenant le FC
    :param feature_name: nom (code) de l'objet à extraire
    :return:
    """

    liste_f = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_FeatureTypes']
    liste_i = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_InformationTypes']

def extr_roles (data_dict):
    """
    extract roles from FC.xml
    :param data_dict:
    :return:
    """

    try:
        liste_roles = data_dict['S100FC:S100_FC_FeatureCatalogue']['S100FC:S100_FC_Roles']['S100FC:S100_FC_Role']
    except:
        print("\tNo roles found in this standard")
        liste_roles = []
    role_index = build_alpha_index(liste_roles,"S100FC:code")

    return role_index

def extr_attr_used_by_feat_info (dict_attr, dict_feat):
    """
    Pour chaque item de dict_attr, regarde dans dict_feat si l'attribut est référencé.
    :param dict_attr: dictionnaire des attributs (simples, complexes ou les deux)
    :param dict_feat: dictionnaire des features + informations
    :return: un dictionnaire avec une clé attr_name et une clé list_feat
    """
    resultat = []

    for attr in dict_attr:
        attr_name = attr["code"]
        list_feat = []
        for feat in dict_feat:
            for feat_attr in feat.get("attributes",[]):
                if feat_attr.get("attribut_name") == attr_name:
                    list_feat.append(feat["code"])
        if list_feat != []:
            resultat.append({
                "name": attr["name"],
                "liste_feat": list_feat
            })
    return resultat

def extr_attr_used_by_complex (dict_attr, dict_complex):
    """

    :param dict_attr:
    :param dict_complex:
    :return:
    """
    resultat = []
    for attr in dict_attr:
        attr_name = attr["code"]
        list_feat = []
        for complex in dict_complex:
            for feat_attr in complex.get("subattributes",[]):
                if feat_attr.get("attribut_name") == attr_name:
                    list_feat.append(complex["code"])
        if list_feat != []:
            resultat.append({
                "name": attr["name"],
                "liste_ac": list_feat
            })
    return resultat

def generate_sidebar(features, informations, associations_index, roles_index):
    """

    :param features: liste des features avec index
    :param informations: liste des informations avec index
    :return: string pour intégration dans fichier xml
    """
    parts = ['<div class="sidebar" style="resize: horizontal; overflow: auto;"><h2 id="s_features">Feature Types</h2><ul>']
    for ft in features:
        for i in features[ft]:
            parts.append(f'<li><a href="#feature_{i["code"]}">{i["name"]}</a></li>')

    parts.append('</ul><h2 id="s_informations">Information Types</h2><ul>')
    for info in informations:
        for i in informations[info]:
            parts.append(f'<li><a href="#info_{i["code"]}">{i["name"]}</a></li>')
    parts.append('</ul>')

    parts.append('</ul><h2 id="s_associations">Associations</h2><ul>')
    for letter, asso_list in associations_index.items():
        for i in asso_list:
            parts.append(f'<li><a href="#asso_{i["S100FC:code"]}">{i["S100FC:name"]}</a></li>')

    parts.append('</ul><h2 id="s_roles">Roles</h2><ul>')
    for letter, role_list in roles_index.items():
        for i in role_list:
            parts.append(f'<li><a href="#r_{i["S100FC:code"]}">{i["S100FC:name"]}</a></li>')

    parts.append('</ul></div>')

    return ''.join(parts)

def generate_top_nav(feature_index, attribute_index, information_index, association_index, role_index):
    parts = ['<div class="top-nav">']
    parts.append('<div><strong><a href="#s_features">Features:</a></strong> ' + ''.join(f'<a href="#f_letter_{l}">{l}</a>' for l in feature_index) + '<br>')
    parts.append('<strong><a href="#s_informations">Informations:</a></strong> ' + ''.join(f'<a href="#i_letter_{l}">{l}</a>' for l in information_index) + '<br>')
    parts.append('<strong><a href="#s_associations">Associations:</a></strong> ' + ''.join(f'<a href="#asso_letter_{l}">{l}</a>' for l in association_index) + '<br>')

    parts.append('</div>')
    parts.append('<div><strong><a href="#a_details">Attributes:</a></strong> ' + ''.join(f'<a href="#a_letter_{l}">{l}</a>' for l in attribute_index) + '<br>' )
    parts.append('<strong><a href="#s_roles">Roles:</a></strong> ' + ''.join(f'<a href="#role_letter_{l}">{l}</a>' for l in role_index))
    parts.append('</div>')
    parts.append('</div>')
    return ''.join(parts)

def generate_left_column(feature_index,
                         information_index,
                         attribute_dict,
                         association_index):
    """
    v beta pour remplacer plus haut (qui fonctionne mais il y a plus de chose dans beta)
    :param feature_index:
    :param information_index:
    :param attribute_dict:
    :param association_index:
    :param role_index:
    :return:
    """

    parts = ['<div class="column"><h2>Feature Details</h2>']
    for letter, ft_list in feature_index.items():
        parts.append(f'<h3 id="f_letter_{letter}"></h3>')
        for ft in ft_list:
            if not ft['alias']:
                alias = ''
            else:
                alias = ' - ' + str(ft['alias'])
                alias = alias.replace("[","").replace("]","").replace("'","")
                print("pour FEATURE : ", alias)

            parts.append(f'<h4 id="feature_{ft["code"]}">{ft["name"]} ({ft["code"]} ) {alias}</h4>')
            parts.append(f'<p><strong>Definition:</strong> {ft["definition"]}</p>')
            # TODO: f statemanet
            parts.append(f'<p><strong>Primitive:</strong> {list_to_string(ft["primitive"])}</p>')
            #parts.append(f'<p><strong>Primitive:</strong> {str(ft["primitive"]).replace("[","").replace("]","").replace("'","")}</p>')

            if ft["supertype"] != '':
                parts.append(f'<p><strong>Inherited from : </strong><a href="#feature_{ft["supertype"]}">{ft["supertype"]}</a></p> ')
            if ft["attributes"]:
                parts.append('<p><strong>Attributes:</strong><ul>')
                for attr in ft["attributes"]:
                    attr_name = ft['name']
                    ref_code=attr["attribut_name"]
                    lower = attr["lower"]
                    upper = attr["upper"]
                    infini = upper['infini']
                    val = upper['val']
                    if val is None and infini == 'false':
                        pass
                    if val is None:
                        val = '*'
                    if attr['permitted_values'] is not None:
                        if isinstance(attr['permitted_values']['permitted_values'],list):
                            machaine = ", ".join(attr['permitted_values']['permitted_values'])
                        else:
                            machaine = attr['permitted_values']['permitted_values'].replace("'","")
                        machaine = '<br>&emsp;permitted values : ' + machaine
                    else:
                        machaine = ''

                    for elem in attribute_dict:
                        if elem["code"] == ref_code:
                            attr_name = elem["name"]
                    if attr_name:
                        parts.append(f'<li><a href="#attr_{ref_code}">{attr_name} ({ref_code})</a> [{lower},{val}]{machaine}</li>')
                    else:
                        parts.append(f'<li>{ref_code}</li>')
                parts.append('</ul></p>')

            if ft["assos_f"]:
                parts.append('<p><strong>Can be associated with feature(s):</strong><ul>')
                for i in ft["assos_f"]:
                    try:
                        feat = i['S100FC:featureType']['@ref']
                    except:
                        feat = []
                        for j in i['S100FC:featureType']:
                            feat.append(j['@ref'])
                    asso = i['S100FC:association']['@ref']
                    role = i['S100FC:role']['@ref']
                    lower = i['S100FC:multiplicity']['S100Base:lower']
                    upper = extr_upper(i['S100FC:multiplicity']['S100Base:upper'])
                    infini = upper['infini']
                    val = upper['val']
                    if val is None and infini == 'false':
                        pass
                        print("upper non defini et n'est pas infini")
                    if val is None:
                        val = '*'
                    parts.append(f'<li>')
                    if isinstance(feat, str):
                        parts.append(f'<a href="#feature_{feat}">{feat}</a> ')
                    elif isinstance(feat, list):
                        for j in feat:
                            parts.append(f'<a href="#feature_{j}">{j}</a>, ')
                    else:
                        feat = ''
                    parts.append(
                        f' via <a href="#asso_{asso}">{asso}</a> as <a href="#r_{role}">{role}</a> role [{lower},{val}]</li>')
                parts.append('</ul></p>')
            if ft["assos_i"]:
                parts.append('<p><strong>Can be associated with information(s):</strong><ul>')
                for i in ft["assos_i"]:
                    try:
                        feat = i['S100FC:informationType']['@ref']
                        #print("test reference : ",feat)
                    except:
                        if isinstance(['S100FC:informationType'],list):
                            #print("pb except 1", i['S100FC:informationType'] )
                            feat = []
                            for j in i['S100FC:informationType']:
                                feat.append(j['@ref'])

                    asso = i['S100FC:association']['@ref']
                    role = i['S100FC:role']['@ref']
                    lower = i['S100FC:multiplicity']['S100Base:lower']
                    upper = extr_upper(i['S100FC:multiplicity']['S100Base:upper'])
                    infini = upper['infini']
                    val = upper['val']
                    if val is None and infini == 'false':
                        pass
                        print("upper non defini et n'est pas infini")
                    if val is None:
                        val = '*'
                    parts.append(f'<li>')
                    if isinstance(feat,str):
                        parts.append(f'<a href="#info_{feat}">{feat}</a> ')
                    elif isinstance(feat,list):
                        for j in feat:
                            parts.append(f'<a href="#info_{j}">{j}</a>, ')
                    else:
                        feat=''
                    parts.append(f' via <a href="#asso_{asso}">{asso}</a> as <a href="#r_{role}">{role}</a> role [{lower},{val}]</li>')
                parts.append('</ul></p>')

    parts.append('<h2>Information Types</h2>')
    for letter, inf_list, in information_index.items():
        parts.append(f'<h3 id="i_letter_{letter}"></h3>')
        for info in inf_list:
            if not info['alias']:
                alias = ''
            else:
                alias = ' - ' + str(info['alias'])
                alias = alias.replace("[","").replace("]","").replace("'","")
            parts.append(f'<h4 id="info_{info["code"]}">{info["name"]} ({info["code"]}) {alias}</h4>')
            parts.append(f'<p><strong>Definition:</strong> {info["definition"]}</p>')
            if info["attributes"]:
                parts.append('<p><strong>Attributes:</strong><ul>')
                for ref_code in info["attributes"]:

                    ref_code_name=ref_code["attribut_name"]
                    lower = ref_code["lower"]
                    upper = ref_code["upper"]
                    infini = upper['infini']
                    val = upper['val']
                    if val is None and infini == 'false':
                        pass
                        print("upper non defini et n'est pas infini")
                    if val is None:
                        val = '*'

                    for elem in attribute_dict:
                        if elem["code"] == ref_code:
                            attr_name = elem["name"]
                    if attr_name:
                        parts.append(f'<li><a href="#attr_{ref_code_name}">{ref_code_name}</a> [{lower},{val}]</li>')
                    else:
                        parts.append(f'<li>{ref_code}</li>')
                parts.append('</ul></p>')
                if info["assos_f"]:
                    parts.append('<p><strong>Can be associated with feature(s):</strong><ul>')
                    for i in info["assos_f"]:
                        try:
                            feat = i['S100FC:featureType']['@ref']
                        except:
                            if isinstance(i['S100FC:informationType'], list):
                                if len(i['S100FC:informationType']) == 0:
                                    feat = ''
                                else:
                                    # print(i['S100FC:informationType'])
                                    liste_ref = []
                                    for k in i['S100FC:informationType']:
                                        liste_ref.append(k['@ref'])
                                    feat = liste_ref
                            else:
                                feat = ''
                        asso = i['S100FC:association']['@ref']
                        role = i['S100FC:role']['@ref']
                        lower = i['S100FC:multiplicity']['S100Base:lower']
                        upper = extr_upper(i['S100FC:multiplicity']['S100Base:upper'])
                        infini = upper['infini']
                        val = upper['val']
                        if val is None and infini == 'false':
                            pass
                            print("upper non defini et n'est pas infini")
                        if val is None:
                            val = '*'
                        if isinstance(feat,list):
                            for k in feat:
                                parts.append(
                                    f'<li><strong><a href="#info_{k}">{k}</a></strong> via <a href="#asso_{asso}">{asso}</a> as <a href="#r_{role}">{role}</a> role [{lower},{val}]</li>')
                        elif isinstance(feat,str):
                            parts.append(
                                f'<li><strong><a href="#info_{feat}">{feat}</a></strong> via <a href="#asso_{asso}">{asso}</a> as <a href="#r_{role}">{role}</a> role [{lower},{val}]</li>')
                        else:
                            pass
                    parts.append('</ul></p>')
                if info["assos_i"]:
                    parts.append('<p><strong>Can be associated with information(s):</strong><ul>')
                    for i in info["assos_i"]:
                        try:
                            feat = i['S100FC:informationType']['@ref']
                        except:
                            # print("pb d'association ")
                            if isinstance(i['S100FC:informationType'], list) :
                                if len(i['S100FC:informationType']) == 0:
                                    feat = ''
                                else:
                                    #print(i['S100FC:informationType'])
                                    liste_ref = []
                                    for k in i['S100FC:informationType']:
                                        liste_ref.append(k['@ref'])
                                    feat = liste_ref
                            else:
                                feat=''
                        asso = i['S100FC:association']['@ref']
                        try:
                            role = i['S100FC:role']['@ref']
                        except:
                            print(f'\tNo role defined for association {asso}')
                            role = ''
                        lower = i['S100FC:multiplicity']['S100Base:lower']
                        upper = extr_upper(i['S100FC:multiplicity']['S100Base:upper'])
                        infini = upper['infini']
                        val = upper['val']
                        if val is None and infini == 'false':
                            pass
                            print("upper non defini et n'est pas infini")
                        if val is None:
                            val = '*'
                        if isinstance(feat,list):
                            for k in feat:
                                parts.append(
                                    f'<li><strong><a href="#info_{k}">{k}</a></strong> via <a href="#asso_{asso}">{asso}</a> as <a href="#r_{role}">{role}</a> role [{lower},{val}]</li>')
                        elif isinstance(feat,str):
                            parts.append(
                                f'<li><strong><a href="#info_{feat}">{feat}</a></strong> via <a href="#asso_{asso}">{asso}</a> as <a href="#r_{role}">{role}</a> role [{lower},{val}]</li>')
                        else:
                            pass
                    parts.append('</ul></p>')

    parts.append('<h2>Associations</h2>')
    for letter, ass_list, in association_index.items():
        parts.append(f'<h3 id="asso_letter_{letter}"></h3>')
        for asso in ass_list:
            parts.append(f'<h4 id="asso_{asso["S100FC:code"]}">{asso["S100FC:name"]} ({asso["S100FC:code"]})</h4>')
            try:
                type = asso["type"]
            except:
                print('pas de type pour association :',asso['S100FC:code'])
                type = 'Unknown'
            if type == 'feature2feature':
                type = 'feature - feature'
            elif type == 'feature2information':
                type = 'feature - information'
            else:
                type == 'Unknown'
            parts.append(f'<p><strong>Association type:</strong> {type}</p>')
            parts.append(f'<p><strong>Definition:</strong> {asso["S100FC:definition"]}</p>')
            maliste = []
            if isinstance(asso['S100FC:role'],list):
                for role in asso['S100FC:role']:
                    # TODO: f statemanet
                    role_str = f'<a href="#r_{role["@ref"]}">{role["@ref"]}</a>'
                    maliste.append(role_str)
            else:
                # TODO: f statemanet
                role_str =  f'<a href="#r_{asso["S100FC:role"]["@ref"]}">{asso["S100FC:role"]["@ref"]}</a>'
                maliste.append(role_str)

            machaine = ", ".join(maliste)
            parts.append(f'<p><strong>Roles:</strong> {machaine}')

    parts.append('</div>')

    return ''.join(parts)

def test_name_index (code, index):
    """
    test si code est dans index (information_index, feature_index)
    :param code: str
    :param index:
    :return: True ou False
    """

    #print(index)

    liste_nom = []
    for letter, attr_list in index.items():
        for i in attr_list:
            liste_nom.append(i['code'])
    if code in liste_nom:
        valeur = True
    else:
        valeur = False
    return valeur

def generate_right_column(attribute_index,feature_index,information_index,role_index):
    """
    :param attribute_index:
    :return:
    """
    parts = ['<div class="column"><h2 id="a_details" >Attributes Details</h2>']

    for letter, attr_list in attribute_index.items():
        parts.append(f'<h3 id="a_letter_{letter}"></h3>')
        for attr in attr_list:
            if attr["alias"] != None:
                alias = str(attr["alias"]).replace("[","").replace("]","").replace("'","")
                str_alias = f" - {alias}"
            else:
                str_alias = ""
            parts.append(f'<h4 id="attr_{attr["code"]}">{attr["name"]} ({attr["code"]}){str_alias}</h4>')
            parts.append(
                f"<p><strong>Type:</strong> {attr['type']}<br><strong>Definition:</strong> {attr['definition']}</p>")
            if attr['type'] == 'complex' and attr.get('subattributes'):
                parts.append('<p><strong>Composed of:</strong><ul>')
                for subref in attr['subattributes']:
                    sub_attr = subref['attribut_name']
                    lower = subref["lower"]
                    upper = subref["upper"]
                    infini = upper['infini']
                    val = upper['val']
                    if val is None and infini == 'false':
                        pass
                        print("upper non defini et n'est pas infini")
                    if val is None:
                        val = '*'
                    if sub_attr:
                        parts.append(f'<li><a href=\"#attr_{sub_attr}\">{sub_attr}</a> [{lower},{val}]</li>')
                    else:
                        parts.append(f'<li>{subref}</li>')
                parts.append('</ul></p>')

            if 'listed_values' in attr:
                if attr["listed_values"] != []:
                    parts.append('<table><tr><th>Label</th><th>Code</th><th>Definition</th></tr>')
                    for i in attr['listed_values']:
                        label = i["label"]
                        code_val = i["code"]
                        value_def = i["definition"]
                        parts.append(f"<tr><td>{label}</td><td>{code_val}</td><td>{value_def}</td></tr>")
                parts.append('</table>')

            if attr['used_by'] != []:
                parts.append('<p><strong>Used by:</strong><ul>')
                for i in attr['used_by']:
                    for j in i["liste_feat"]:
                        if test_name_index(j,information_index):
                            parts.append(f'<li><a href="#info_{j}">{j}</a></li>')
                        else:
                            parts.append(f'<li><a href="#feature_{j}">{j}</a></li>')
                parts.append(f'</ul>')
            if attr['used_by_compl'] != []:
                parts.append('<p><strong>Used by complex attribute(s):</strong><ul>')
                for i in attr['used_by_compl']:
                    for j in i["liste_ac"]:
                        parts.append(f'<li><a href="#attr_{j}">{j}</a></li>')
                parts.append(f'</ul>')

    parts.append('<h2>Roles</h2>')

    for letter, role_list, in role_index.items():
        parts.append(f'<h3 id="role_letter_{letter}"></h3>')
        for role in role_list:
            parts.append(f'<h4 id="r_{role["S100FC:code"]}">{role["S100FC:name"]} ({role["S100FC:code"]})</h4>')
            parts.append(f'<p><strong>Definition:</strong> {role["S100FC:definition"]}</p>')

    parts.append('</div>')
    return ''.join(parts)

def wrap_html_page(title,sidebar, top_nav, left_column, right_column):
    return '\n'.join([
        '<html><head><title>',title,'</title><meta charset="UTF-8">',
        '<style>',
        'body { font-family: Arial; margin: 0; display: flex; height: 100vh; overflow: hidden; }',
        '.sidebar { width: 250px; background: #f4f4f4; padding: 20px; overflow-y: auto; border-right: 1px solid #ccc; }',
        '.sidebar h2 { font-size: 1.2em; color: #003366; margin-top: 0; }',
        '.sidebar ul { list-style: none; padding-left: 0; }',
        '.sidebar li { margin: 5px 0; }',
        '.sidebar a { text-decoration: none; color: #003366; }',
        '.sidebar a:hover { text-decoration: underline; }',
        '.content { flex: 1; display: flex; flex-direction: column; }',
        '.columns { display: flex; flex: 1; overflow: hidden; }',
        '.column { width: 50%; padding: 20px; overflow-y: auto; }',
        '.top-nav { display: flex; justify-content: space-between; background: #eaeaea; padding: 10px 20px; border-bottom: 1px solid #ccc; font-size: 14px; }',
        '.top-nav a { margin-right: 10px; color: #003366; text-decoration: none; }',
        '.top-nav a:hover { text-decoration: underline; }',
        'table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }',
        'th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }',
        'th { background: #e0e0e0; }',
        'h1 { padding: 20px; background: #003366; color: white; margin: 0; width: 100%; }',
        'h4 { background: grey; color: white; padding: 10px;}',
        '</style></head><body>',
        '<div style="position: fixed; top: 0; left: 0; right: 0;"><h1>',title,'</h1></div>',
        '<div style="display: flex; width: 100%; margin-top: 70px;">',
        sidebar,
        '<div class="content">',
        top_nav,
        '<div class="columns">',
        left_column,
        right_column,
        '</div></div></div></body></html>'
    ])

def generate_html_from_fc (title, data_dict):

    #extraction des infos
    mes_objets = extr_features_infos(data_dict,'features')
    mes_informations = extr_features_infos(data_dict,'informations')
    mes_ac = extr_attributs_complex(data_dict)
    mes_attr = extr_attributs_simpl(data_dict)
    mes_asso = extr_associations(data_dict)
    mes_roles = extr_roles(data_dict)


    # extraction des utilisations
    attrs = mes_ac + mes_attr
    objets = mes_objets + mes_informations
    used_by = extr_attr_used_by_feat_info (attrs, objets)
    used_by_compl = extr_attr_used_by_complex(attrs, mes_ac)

    # jointure de attrs avec used_by
    used_by_index = {}
    for item in used_by:
        used_by_index.setdefault(item["name"], []).append(item)
    for attr in attrs:
        name = attr["name"]
        attr["used_by"] = used_by_index.get(name, [])

    #jointure de attrs avec used_by_compl
    used_by_compl_index = {}
    for item in used_by_compl:
        used_by_compl_index.setdefault(item["name"], []).append(item)
    for attr in attrs:
        name = attr["name"]
        attr["used_by_compl"] = used_by_compl_index.get(name, [])

    #print("contruction index features")
    # les index devraient être construits dans les fonctions (le cas pour les associations)
    feature_index = build_alpha_index(mes_objets, "name")
    #print("contruction index info")
    information_index = build_alpha_index(mes_informations, "name")
    #print("contruction index attr")
    attribute_index = build_alpha_index(attrs, "name")


    # print("liste des informations :")
    # print(mes_informations)
    # print("liste des objets :")
    # print(mes_objets)
    # print("liste des attributs simples :")
    # print(mes_attr)
    # print("liste des attributs complexes :")
    # print(mes_ac)
    # print("liste des associations")
    # print(mes_asso)
    # print("liste des rôles")
    # print(mes_roles)
    # print("attribut utilisés par :")
    # print(used_by)
    # print("attribut utilisés par attr complexes :")
    # print(used_by_compl)
    # print('----------------------------')
    # print("info index : ",information_index)
    sidebar = generate_sidebar(feature_index, information_index, mes_asso, mes_roles)
    top_nav = generate_top_nav(feature_index,attribute_index, information_index, mes_asso, mes_roles)
    # print("attribute index :",attribute_index)
    right_column = generate_right_column(attribute_index,feature_index,information_index,mes_roles)

    attribute_dict = attrs
    association_dict_idx = mes_asso
    left_column = generate_left_column(feature_index, information_index, attribute_dict, association_dict_idx)
    html_content = wrap_html_page(title,sidebar, top_nav, left_column, right_column)

    return html_content

def xml_data_dict(fic_in):
    """

    :param fic_in:
    :return:
    """
    with open(fic_in, encoding="utf-8") as xml_file:
        lines = xml_file.readlines()[1:]  # saute la première ligne
        content = "".join(lines)
        data_dict = xmltodict.parse(content)
        return data_dict

    return None

def list_to_string(lst, sep=', '):
    """

       :param lst:
       :param sep:
       :return:
       """
    if isinstance(lst,list):
        return sep.join(lst)
    elif isinstance(lst, str):
        return lst
    else:
        return None

def write_html(fic_out, html_content):
    """

    :param fic_out:
    :param html_content:
    """
    with open(fic_out, 'w', encoding='utf-8') as f:
        f.write(html_content)

def cr_file(fic_in):
    """
    run the html creation for one file
    fic_in : input file
    """
    fic_name = os.path.basename(os.path.splitext(fic_in)[0])
    folder_out = os.path.dirname(fic_in)
    data_dict = xml_data_dict(fic_in)

    general = extr_title(data_dict)
    try:
        norme = general['productId']
    except:
        norme = "productId not "
    version = general['version']
    title = norme + " - " + general['name'] + ' - Feature Catalog v.' + version

    html_content = generate_html_from_fc(title, data_dict)

    fic_out = fic_name + '.htm'
    new_file = os.path.join(folder_out, fic_out)
    write_html(new_file, html_content)

    print(f'... done creating {new_file}')

def cr_files(dir_in):
    """ create all FC.html from a folder containing FC.xml, in the same one"""
    if not os.path.exists(dir_in):
        print(f"folder {dir_in} does not exist")
    elif not os.path.isdir(dir_in):
        print(f"{dir_in} is not a directory")
    else:
        print("folder exists ok")
        fichiers_in = []
        try:
            for fichier in os.listdir(dir_in):
                extension = os.path.splitext(fichier)[-1]
                if extension.lower() == (".xml"):
                    fichiers_in.append(os.path.join(dir_in,fichier))
                else:
                    print(f'file {fichier} not xml')
        except:
            print("\033[33mfile access issue (perm?)\033[0mm")
        #print("liste des fichiers à traiter :")
        for i in fichiers_in:
            print(f"Processing file {i}")
            try:
                cr_file(i)
            except Exception as e:
                print(f'\033[32missue with file création {i}\033[0m')
                print(f"{type(e).__name__} : {e}")
                traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(
        description="specify a file OR a directory."
    )

    # Groupe d'options mutuellement exclusives
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-f", "--file",
        type=str,
        help="file path (ex: -f myfile.txt)"
    )
    group.add_argument(
        "-d", "--directory",
        type=str,
        help="directory path (ex: -d mydir)"
    )

    args = parser.parse_args()

    # Vérification de l'existence du fichier ou du dossier
    if args.file:
        if not os.path.isfile(args.file):
            parser.error(f"Le fichier '{args.file}' n'existe pas.")
        print(f"Fichier sélectionné : {args.file}")
        # Ajoute ici la logique pour traiter le fichier
        cr_file(args.file)

    elif args.directory:
        if not os.path.isdir(args.directory):
            parser.error(f"Le dossier '{args.directory}' n'existe pas.")
        print(f"Dossier sélectionné : {args.directory}")
        # Ajoute ici la logique pour traiter le dossier
        cr_files(args.directory)


if __name__ == "__main__":
    main()
