import os
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml
import pprint

"""
index.html creation to list the files
if no html file in the folder, index empty created
must run FC2html.py before
"""


def ret_info(fichier,tag):
    """
    pour extraire les mtd du fichier
    :param fichier: str, fichier
    :param tag: str, nom du tag à trouver
    :return:
    """
    try:
        tree = ET.parse(fichier)
        root = tree.getroot()

        # Détection auto du namespace principal
        if "}" in root.tag:
            ns = {"x": root.tag.split("}")[0].strip("{")}
            elem = root.find(f".//x:{tag}", ns)
        else:
            elem = root.find(f".//{tag}")
        return elem.text

    except Exception as e:
        print(f"nothing found to process : {e}")
        return None
def list_fichiers(folder,extension):
    """
    sort la liste des fichier xml et html
    sous forme de dict
    html_file :
    xml_file :
    """
    #print(folder)
    try:
        return [
            f for f in os.listdir(folder)
            if f.lower().endswith(extension)
               and os.path.isfile(os.path.join(folder, f))
        ]
    except FileNotFoundError:
        print(f"No files found in {folder}")
        return []
def cr_catalogues(folder,extension_html):
    """creation liste des fichier pour un dossier"""
    liste_dict_fichiers = []
    liste_html = list_fichiers(folder, extension_html)

    for i in liste_html:
        titre=''
        fichier_xml=''
        version=''
        norme=''

        fichier_html = i
        #print(f'pour {i}')
        fichier_xml = i.replace(extension_html, '.xml')
        fichier_xml = os.path.join(folder, fichier_xml)

        if os.path.isfile(fichier_xml):
            #print(f'\tfichier xml correspondant au fichier html {i} existe')
            titre = ret_info(fichier_xml,'name')
            version = ret_info(fichier_xml,'versionNumber')
            norme = ret_info(fichier_xml,'productId')

        else:
            #print(f'\tfichier xml demandé n existe pas {fichier_xml} ')
            fichier_xml =''
            titre = ''

        data = {
            "fichier_html": fichier_html,
            "fichier_xml": i.replace(extension_html, '.xml'),
            "titre": titre,
            "version": version,
            "norme": norme
        }
        liste_dict_fichiers.append(data)
    #print(liste_dict_fichiers, len(liste_dict_fichiers))
    return liste_dict_fichiers

    return catalogues
def render_section(titre, catalogue, folder):
    rows = []

    for cat in catalogue:
        #print("cat : ",cat)
        dossier = folder.split("\\")[-1]
        lien_xml = './' + dossier + '/' + cat['fichier_xml'].split("\\")[-1]
        lien_html = './' + dossier + '/' + cat['fichier_html'].split("\\")[-1]
        rows.append(f"""
        <tr>
            <td>{cat['norme']}</td>
            <td><a href={lien_html}>{cat['titre']}</a></td>
            <td>{cat['version']}</td>
            <td><a href="./{lien_xml}">XML</a></td>
        </tr>
        """)

    return f"""
    <section>
        <h2>{titre}</h2>
        <table>
            <thead>
                <tr>
                    <th>Standard</th>
                    <th>Product</th>
                    <th>Version</th>
                    <th>FC.xml</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    </section>
    """

def read_conf(conf_file):
    """
    read the config file and load it into a dict
    :param conf_file:
    :return:
    """
    with open(conf_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config
def main():
    conf = read_conf("config.yaml")
    pprint.pprint(conf)
    BASE_DIR = Path(conf['website']['basedir'])
    TITLE = conf['website']['name']
    OFFICIAL_DIR = BASE_DIR / conf['website']['dirs']['official_dir']
    DEV_DIR = BASE_DIR / conf['website']['dirs']['dev_dir']
    OUTPUT_HTML =  BASE_DIR / conf['website']['output_html']
    extension_html = conf['website']['html_extension']
    date_creation = date.today().strftime("%d/%m/%Y")

    fichiers_officiels = cr_catalogues(OFFICIAL_DIR,extension_html)
    fichiers_dev = cr_catalogues(DEV_DIR,extension_html)


    #creation html
    html = []
    html.append("""
    <!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">""")
    html.append(f"""<title>{TITLE}</title>""")
    html.append("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        :root {
            --primary: #003a8f;
            --secondary: #0066cc;
            --background: #f4f6f8;
            --card: #ffffff;
            --text: #2c2c2c;
            --muted: #6c757d;
        }

        body {
            margin: 0;
            font-family: "Segoe UI", Arial, Helvetica, sans-serif;
            background-color: var(--background);
            color: var(--text);
        }

        header {
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            color: white;
            padding: 2.5rem 2rem;
            text-align: center;
        }

        header h1 {
            margin: 0;
            font-size: 2.2rem;
        }

        header p {
            margin-top: 0.8rem;
            font-size: 1.1rem;
            opacity: 0.95;
        }

        main {
            max-width: 1100px;
            margin: 3rem auto;
            padding: 0 1.5rem;
        }

        section {
            background-color: var(--card);
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        section h2 {
            margin-top: 0;
            color: var(--primary);
            border-bottom: 3px solid #e3e7eb;
            padding-bottom: 0.6rem;
        }

        section p.description {
            margin: 1rem 0 1.5rem 0;
            color: var(--muted);
            font-size: 0.95rem;
        }

        ul {
            list-style: none;
            padding-left: 0;
        }

        li {
            margin: 0.8rem 0;
        }

        a {
            text-decoration: none;
            color: var(--secondary);
            font-weight: 500;
        }

        a:hover {
            text-decoration: underline;
        }

        footer {
            background-color: #e9ecef;
            padding: 1.2rem;
            text-align: center;
            font-size: 0.85rem;
            color: var(--muted);
        }

        footer span {
            color: var(--primary);
            font-weight: 600;
        }
    </style>
</head>""")
    html.append(f"""
<body>

<header>
    <h1>S-100 Feature Catalogs</h1>
    <p>S-100 PS explorer : Tool to explore S-100 standards</p>
    <p>created {date_creation} </p>
</header>

<main>

    """)
    html.append(render_section("FC in development", fichiers_dev, str(DEV_DIR)))
    html.append(render_section("Official FC", fichiers_officiels, str(OFFICIAL_DIR)))
    html.append("""<section>
            <h2>Portrayal</h2>
            <p class="description">
             <ol>
                <li><a href="./divers/colorprofile.html"> Preview S-100 colors</a></li>
                <li><a href="./divers/S-102_colors.html"> S-102 colors</a></li>
                <li><a href="./divers/S101_symbols_table.html">S-101 Symbols preview</a></li>
                <li><a href="./divers/S124_symbol_preview.html">S-124 Symbols preview</a></li>
            </ol>
            </p>

           
                
            </section>""")
    html.append("""<section>
        <h2>Notes</h2>
        <p class="description">
            Les catalogues d’objets officiellement publiés sont téléchargés depuis le <a href="https://registry.iho.int/productspec/list.do">registre de l'OHI</a>.
            <br> Les normes en version inférieure à 2.0.0 sont des normes encore en cours de développement et les Feature Catalog peuvent ne pas être matures et présenter des anomalies.
            Les catalogues en développement sont en cours de spécification, d’expérimentation ou de test, et susceptibles d’évoluer. 
            Ces versions ne sont pas destinées à un usage opérationnel. Ils sont téléchargés pour la plupart depuis le <a href="https://github.com/iho-ohi/">github de l'OHI</a>.
            
            N'hésitez pas à contacter <a href="mailto:dodeur@shom.fr">JB Dodeur</a> pour une mise à jour ou créer une issue sur la <a href="https://github.com/iho-ohi/S100Infrastructure/tree/main/S100PS%20Explorer">page github</a>.
        </p>
        <p class="description">
            Official published features catalog (FC) are from the <a href="https://registry.iho.int/productspec/list.do">IHO registry</a>.
            <br> Standards in a version minus than 2.0.0 are still in development, and their FC may not be mature and include errors or mistypos and subjects to regular evolutions.
            These versions are not meant to an operational use. They are, for the most, from the  <a href="https://github.com/iho-ohi/">IHO github</a>.
            <br>Feel free to contact <a href="mailto:dodeur@shom.fr">JB Dodeur</a> for any information, or log an issue on the <a href="https://github.com/iho-ohi/S100Infrastructure/tree/main/S100PS%20Explorer">github page</a>.
        </p>
        <ul>
            </ul>
        </section>""")
    html.append("""
</main>

<footer>
    <span>v1</span>
</footer>

</body>
</html>
""")



    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        html_file = ''.join(html)
        f.write(html_file)

    print(f"Page générée : {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
