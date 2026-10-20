"""Normalized publication records: page list (publications.csv) + Crossref/OpenAlex metadata + tags.

Citation fields (journal abbreviation, volume, issue, pages) come from Crossref when the Crossref title matches the
listed title; otherwise the listed text is kept and the record is reported in reports/publication_metadata.md.
"""
from pathlib import Path
import csv, difflib, html, json, re, urllib.parse
import yaml

ROOT = Path(__file__).resolve().parent

JOURNAL_ABBR = {
    'Nano Letters': 'Nano Lett.', 'Journal of the American Chemical Society': 'J. Am. Chem. Soc.', 'ACS Nano': 'ACS Nano',
    'Science': 'Science', 'The Journal of Chemical Physics': 'J. Chem. Phys.', 'The Journal of Physical Chemistry C': 'J. Phys. Chem. C',
    'Proceedings of the National Academy of Sciences': 'Proc. Natl. Acad. Sci. U.S.A.', 'Physical Review Letters': 'Phys. Rev. Lett.',
    'Physical Review B': 'Phys. Rev. B', 'Chemistry of Materials': 'Chem. Mater.', 'The Journal of Physical Chemistry B': 'J. Phys. Chem. B',
    'Advanced Materials': 'Adv. Mater.', 'Nature': 'Nature', 'Nature Materials': 'Nat. Mater.', 'Nature Communications': 'Nat. Commun.',
    'Angewandte Chemie International Edition': 'Angew. Chem., Int. Ed.', 'The Journal of Physical Chemistry Letters': 'J. Phys. Chem. Lett.',
    'The Journal of Physical Chemistry': 'J. Phys. Chem.', 'ACS Photonics': 'ACS Photonics', 'Nanotechnology': 'Nanotechnology',
    'MRS Bulletin': 'MRS Bull.', 'Langmuir': 'Langmuir', 'Applied Physics Letters': 'Appl. Phys. Lett.', 'Science Advances': 'Sci. Adv.',
    'Advanced Functional Materials': 'Adv. Funct. Mater.', 'Chemical Physics Letters': 'Chem. Phys. Lett.',
    'Accounts of Chemical Research': 'Acc. Chem. Res.', 'Digital Discovery': 'Digital Discovery', 'Journal of Chemical Education': 'J. Chem. Educ.',
    'Nano Research': 'Nano Res.', 'IEEE Journal of Photovoltaics': 'IEEE J. Photovoltaics', 'Journal of Visualized Experiments': 'J. Visualized Exp.',
    'ACS Central Science': 'ACS Cent. Sci.', 'Neuron': 'Neuron', 'Annual Review of Physical Chemistry': 'Annu. Rev. Phys. Chem.',
    'Scientific American': 'Sci. Am.', 'Chemical Communications': 'Chem. Commun.', 'Nature Biotechnology': 'Nat. Biotechnol.',
    'Journal of Applied Physics': 'J. Appl. Phys.', 'Berichte der Bunsengesellschaft für physikalische Chemie': 'Ber. Bunsen-Ges. Phys. Chem.',
    'Zeitschrift für Physik D Atoms, Molecules and Clusters': 'Z. Phys. D', 'Nature Synthesis': 'Nat. Synth.', 'Nature Photonics': 'Nat. Photonics',
    'npj Computational Materials': 'npj Comput. Mater.', 'Frontiers in Photonics': 'Front. Photonics', 'Communications Chemistry': 'Commun. Chem.',
    'Scientific Reports': 'Sci. Rep.', 'ACS Applied Energy Materials': 'ACS Appl. Energy Mater.', 'Nature Nanotechnology': 'Nat. Nanotechnol.',
    'ACS Applied Materials & Interfaces': 'ACS Appl. Mater. Interfaces', 'Journal of Optics': 'J. Opt.', 'Faraday Discussions': 'Faraday Discuss.',
    'Ultramicroscopy': 'Ultramicroscopy', 'Environmental Science & Technology': 'Environ. Sci. Technol.', 'The Journal of Physical Chemistry A': 'J. Phys. Chem. A',
    'Annual Review of Biomedical Engineering': 'Annu. Rev. Biomed. Eng.', 'Analytical Chemistry': 'Anal. Chem.', 'Optics Letters': 'Opt. Lett.',
    'Angewandte Chemie International Edition in English': 'Angew. Chem., Int. Ed. Engl.', 'Catalysis Letters': 'Catal. Lett.',
    'Journal of Biological Chemistry': 'J. Biol. Chem.', 'Biophysical Journal': 'Biophys. J.', 'Catalysis Today': 'Catal. Today',
    'Journal of Synchrotron Radiation': 'J. Synchrotron Radiat.', 'Current Opinion in Neurobiology': 'Curr. Opin. Neurobiol.',
    'Surface Science': 'Surf. Sci.', 'Israel Journal of Chemistry': 'Isr. J. Chem.', 'Solar Energy Materials and Solar Cells': 'Sol. Energy Mater. Sol. Cells',
    'Materials Today Communications': 'Mater. Today Commun.', 'MRS Communications': 'MRS Commun.', 'Synthetic Metals': 'Synth. Met.',
    'Superlattices and Microstructures': 'Superlattices Microstruct.', 'Journal of Non-Crystalline Solids': 'J. Non-Cryst. Solids',
    'Pure and Applied Chemistry': 'Pure Appl. Chem.', 'Surface Review and Letters': 'Surf. Rev. Lett.', 'Phase Transitions': 'Phase Transitions',
    'Cell': 'Cell', 'Matter': 'Matter', 'JACS Au': 'JACS Au', 'Molecular Frontiers Journal': 'Mol. Front. J.',
    'Journal of Biomedicine and Biotechnology': 'J. Biomed. Biotechnol.', 'Reviews in Mineralogy and Geochemistry': 'Rev. Mineral. Geochem.',
    'Materials Science and Engineering: A': 'Mater. Sci. Eng., A', 'IEEE Journal of Selected Topics in Quantum Electronics': 'IEEE J. Sel. Top. Quantum Electron.',
    'Differentiation': 'Differentiation', 'Endeavour': 'Endeavour', 'Systems Biomedicine': 'Syst. Biomed.',
}

# Journal groups offered as filters (label, abbreviations).
JOURNAL_GROUPS = [
    ('science', 'Science and Sci. Adv.', {'Science', 'Sci. Adv.'}),
    ('nature', 'Nature family', {'Nature', 'Nat. Mater.', 'Nat. Commun.', 'Nat. Synth.', 'Nat. Photonics', 'Nat. Nanotechnol.', 'Nat. Biotechnol.', 'Commun. Chem.', 'Sci. Rep.', 'npj Comput. Mater.'}),
    ('jacs', 'J. Am. Chem. Soc.', {'J. Am. Chem. Soc.', 'JACS Au'}),
    ('nanolett', 'Nano Lett.', {'Nano Lett.'}),
    ('acsnano', 'ACS Nano', {'ACS Nano'}),
    ('pnas', 'PNAS', {'Proc. Natl. Acad. Sci. U.S.A.'}),
    ('physrev', 'Phys. Rev.', {'Phys. Rev. Lett.', 'Phys. Rev. B'}),
    ('jpc', 'J. Phys. Chem. and J. Chem. Phys.', {'J. Phys. Chem.', 'J. Phys. Chem. A', 'J. Phys. Chem. B', 'J. Phys. Chem. C', 'J. Phys. Chem. Lett.', 'J. Chem. Phys.'}),
]
REVIEW_JOURNALS = {'Acc. Chem. Res.', 'Annu. Rev. Phys. Chem.', 'Annu. Rev. Biomed. Eng.', 'MRS Bull.', 'Chem. Rev.', 'Chem. Soc. Rev.',
                   'Curr. Opin. Neurobiol.', 'Rev. Mineral. Geochem.'}


def plain(text):
    return html.unescape(re.sub(r'<[^>]+>', '', text or '')).strip()


def norm_title(text):
    return re.sub(r'[^a-z0-9]+', ' ', plain(text).casefold()).strip()


def doi_of(url):
    m = re.search(r'doi\.org/(10\.[^\s?#]+)', url or '')
    return urllib.parse.unquote(m.group(1)).lower() if m else ''


def load():
    rows = list(csv.DictReader((ROOT / 'data/publications.csv').open()))
    works = json.loads((ROOT / 'data/metadata/works.json').read_text()) if (ROOT / 'data/metadata/works.json').exists() else {}
    works = {urllib.parse.unquote(k).lower(): v for k, v in works.items()}
    tags_path = ROOT / 'data/publication_tags.yaml'
    tags = {t['id']: t for t in (yaml.safe_load(tags_path.read_text()) or [])} if tags_path.exists() else {}
    out, report = [], []
    for row in rows:
        doi = doi_of(row['url'])
        w = works.get(doi) or {}
        cr = w.get('crossref') or {}
        oa = w.get('openalex') or {}
        if 'error' in cr:
            cr = {}
        rec = {'id': row['id'], 'group': row['group'], 'year': row['year'], 'doi': doi, 'url': row['url'],
               'title_html': row['title_html'], 'authors_html': row['authors_html'], 'link_label': row['link_label'],
               'journal': plain(row['journal_html']).rstrip(','), 'details': plain(row['details_html']), 'source': 'page'}
        cr_title = plain((cr.get('title') or [''])[0]) if cr.get('title') else ''
        if cr and cr_title:
            ratio = difflib.SequenceMatcher(None, norm_title(cr_title), norm_title(row['title_html'])).ratio()
            if ratio >= 0.8:
                full = html.unescape((cr.get('container-title') or [''])[0]) if cr.get('container-title') else ''
                rec['journal'] = JOURNAL_ABBR.get(full, full or rec['journal'])
                vol, issue = cr.get('volume', ''), cr.get('issue', '')
                pages = (cr.get('page') or cr.get('article-number') or '').replace('-', '–')
                parts = []
                if vol:
                    parts.append(f'{vol} ({issue})' if issue else vol)
                if pages:
                    parts.append(pages)
                rec['details'] = ', '.join(parts)
                rec['source'] = 'crossref'
            else:
                report.append((row['id'], row['year'], doi, f'title mismatch {ratio:.2f}', plain(row['title_html'])[:90], cr_title[:90]))
        elif doi:
            report.append((row['id'], row['year'], doi, 'no Crossref record', plain(row['title_html'])[:90], ''))
        ctype = (oa.get('type') or '').lower()
        if rec['journal'] in REVIEW_JOURNALS or ctype == 'review':
            rec['type'] = 'review'
        elif ctype == 'editorial' or (cr.get('subtype') or '') in ('editorial', 'commentary'):
            rec['type'] = 'perspective'
        else:
            rec['type'] = 'article'
        # Open access by journal: only papers in fully open-access journals (OpenAlex source.is_oa; gold or diamond).
        # Free copies in repositories (green), free-to-read (bronze) and hybrid articles do not count (Dylan, 2026-10-20).
        rec['oa'] = bool(((oa.get('primary_location') or {}).get('source') or {}).get('is_oa'))
        rec['journal_group'] = next((slug for slug, _, names in JOURNAL_GROUPS if rec['journal'] in names), '')
        rec['crossref_authors'] = [' '.join(x for x in (a.get('given', ''), a.get('family', '')) if x) for a in (cr.get('author') or [])] if rec['source'] == 'crossref' else []
        t = tags.get(row['id']) or {}
        for facet in ('areas', 'materials', 'approaches', 'applications'):
            rec[facet] = [x['tag'] if isinstance(x, dict) else x for x in (t.get(facet) or [])]
        out.append(rec)
    return out, report
