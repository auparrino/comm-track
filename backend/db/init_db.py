"""
Pisubí — Inicialización de base de datos
Crea las tablas y carga datos semilla (commodities, empresas, actores).
"""
import sqlite3
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    print("[DB] Schema aplicado.")


def seed_commodities(conn: sqlite3.Connection) -> None:
    supply_chains = {
        "lithium": {
            "nodes": ["Salmuera/Roca", "Extracción", "Concentrado",
                      "Carbonato Li₂CO₃", "Hidróxido LiOH", "Celdas batería", "EV/Storage"],
            "edges": [["Salmuera/Roca","Extracción"], ["Extracción","Concentrado"],
                      ["Concentrado","Carbonato Li₂CO₃"], ["Concentrado","Hidróxido LiOH"],
                      ["Carbonato Li₂CO₃","Celdas batería"], ["Hidróxido LiOH","Celdas batería"],
                      ["Celdas batería","EV/Storage"]],
        },
        "gold": {
            "nodes": ["Exploración", "Minería", "Procesamiento", "Refinación",
                      "Joyería", "Inversión", "Industria", "Bancos Centrales"],
            "edges": [["Exploración","Minería"], ["Minería","Procesamiento"],
                      ["Procesamiento","Refinación"], ["Refinación","Joyería"],
                      ["Refinación","Inversión"], ["Refinación","Industria"],
                      ["Refinación","Bancos Centrales"]],
        },
        "soy": {
            "nodes": ["Producción campo", "Acopio/Puertos", "Crushing/Aceiteras",
                      "Aceite crudo", "Harina/Pellets", "Biodiesel", "Consumo interno", "Exportación"],
            "edges": [["Producción campo","Acopio/Puertos"], ["Acopio/Puertos","Crushing/Aceiteras"],
                      ["Crushing/Aceiteras","Aceite crudo"], ["Crushing/Aceiteras","Harina/Pellets"],
                      ["Aceite crudo","Biodiesel"], ["Aceite crudo","Consumo interno"],
                      ["Aceite crudo","Exportación"], ["Harina/Pellets","Exportación"],
                      ["Biodiesel","Consumo interno"], ["Biodiesel","Exportación"]],
        },
        "copper": {
            "nodes": ["Extracción/Mina", "Concentrado", "Fundición", "Refinación",
                      "Cobre puro", "Cables/Tuberías", "Electrónica", "EV/Energía renovable"],
            "edges": [["Extracción/Mina","Concentrado"], ["Concentrado","Fundición"],
                      ["Fundición","Refinación"], ["Refinación","Cobre puro"],
                      ["Cobre puro","Cables/Tuberías"], ["Cobre puro","Electrónica"],
                      ["Cables/Tuberías","EV/Energía renovable"], ["Electrónica","EV/Energía renovable"]],
        },
        "natgas": {
            "nodes": ["Yacimiento", "Extracción", "Procesamiento",
                      "Gasoductos", "Distribución", "Consumo industrial",
                      "Generación eléctrica", "Exportación GNL"],
            "edges": [["Yacimiento","Extracción"], ["Extracción","Procesamiento"],
                      ["Procesamiento","Gasoductos"], ["Gasoductos","Distribución"],
                      ["Distribución","Consumo industrial"], ["Distribución","Generación eléctrica"],
                      ["Procesamiento","Exportación GNL"]],
        },
        "wheat": {
            "nodes": ["Producción campo", "Acopio", "Clasificación/Secado",
                      "Molienda", "Harina", "Exportación grano", "Industria alimentaria"],
            "edges": [["Producción campo","Acopio"], ["Acopio","Clasificación/Secado"],
                      ["Clasificación/Secado","Exportación grano"], ["Clasificación/Secado","Molienda"],
                      ["Molienda","Harina"], ["Harina","Industria alimentaria"],
                      ["Exportación grano","Industria alimentaria"]],
        },
        "corn": {
            "nodes": ["Producción campo", "Acopio/Puertos", "Secado/Clasificación",
                      "Exportación grano", "Molienda húmeda", "Almidón/Fructosa",
                      "Forraje/Pellets", "Etanol"],
            "edges": [["Producción campo","Acopio/Puertos"],
                      ["Acopio/Puertos","Secado/Clasificación"],
                      ["Secado/Clasificación","Exportación grano"],
                      ["Secado/Clasificación","Molienda húmeda"],
                      ["Molienda húmeda","Almidón/Fructosa"],
                      ["Molienda húmeda","Forraje/Pellets"],
                      ["Molienda húmeda","Etanol"]],
        },
    }

    commodities = [
        ("lithium", "Litio (Carbonato)", "Lithium Carbonate",
         "USD/ton", "mineral",
         "Carbonato de litio, insumo clave para baterías de ión litio en vehículos eléctricos y almacenamiento de energía.",
         json.dumps(supply_chains["lithium"])),
        ("gold", "Oro", "Gold",
         "USD/oz", "metal_precioso",
         "Metal precioso usado como reserva de valor, en joyería e industria. Argentina es productor relevante en San Juan y Santa Cruz.",
         json.dumps(supply_chains["gold"])),
        ("soy", "Soja", "Soybeans",
         "USD/bu", "agro",
         "Oleaginosa de mayor exportación argentina. Complejo sojero Gran Rosario es el mayor polo de crushing del mundo.",
         json.dumps(supply_chains["soy"])),
        ("copper", "Cobre", "Copper",
         "USD/lb", "mineral",
         "Metal conductor clave para electrificación, construcción y energías renovables. Argentina tiene depósitos en San Juan y Mendoza.",
         json.dumps(supply_chains["copper"])),
        ("natgas", "Gas Natural", "Natural Gas",
         "USD/MMBtu", "energia",
         "Combustible de transición y materia prima industrial. Vaca Muerta (Neuquén) posiciona a Argentina como exportador potencial de GNL.",
         json.dumps(supply_chains["natgas"])),
        ("wheat", "Trigo", "Wheat",
         "USD/bu", "agro",
         "Cereal de exportación con fuerte presencia en la región pampeana. Argentina es tercer exportador mundial de harina de trigo.",
         json.dumps(supply_chains["wheat"])),
        ("corn", "Maíz", "Corn",
         "USD/bu", "agro",
         "Cereal de mayor producción en Argentina tras la soja. Principal destino: exportación de grano y subproductos. Región pampeana lidera la producción.",
         json.dumps(supply_chains["corn"])),
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO commodities
            (id, name_es, name_en, unit, category, description, supply_chain_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, commodities)
    print(f"[DB] Commodities: {len(commodities)} registros.")


def seed_companies(conn: sqlite3.Connection) -> None:
    companies = [
        # --- LITIO ---
        ("lithium", "Albemarle Corporation",      "ALB",   "NYSE",   "USA", None,       None,                 "producer",  0,
         "Mayor productor de litio del mundo. Opera en Chile (Atacama), Australia (Greenbushes) y USA."),
        ("lithium", "SQM (Sociedad Química)",      "SQM",   "NYSE",   "CHL", None,       None,                 "producer",  0,
         "Segundo productor global. Opera en Salar de Atacama, Chile."),
        ("lithium", "Arcadium Lithium",            "ALTM",  "NYSE",   "AUS", "Catamarca","Fénix / Olaroz",     "producer",  1,
         "Fusión Livent + Allkem. Opera Salar del Hombre Muerto (Catamarca) y Olaroz (Jujuy)."),
        ("lithium", "Lithium Americas Corp",       "LAC",   "NYSE",   "CAN", "Jujuy",    "Cauchari-Olaroz",    "producer",  1,
         "50% Cauchari-Olaroz con Ganfeng. Proyecto Thacker Pass en USA."),
        ("lithium", "Piedmont Lithium",            "PLL",   "NASDAQ", "USA", None,       None,                 "producer",  0,
         "Productor emergente USA. Sin operaciones en AR."),
        ("lithium", "Ganfeng Lithium (OTC)",       "GNENF", "OTC",    "CHN", "Jujuy",    "Mariana / Cauchari", "producer",  1,
         "Mayor empresa china de litio. 50% Cauchari-Olaroz, proyecto Mariana (Salta)."),
        ("lithium", "Eramet",                      None,    None,     "FRA", "Salta",    "Centenario-Ratones", "producer",  1,
         "Empresa francesa. Proyecto Centenario-Ratones en Salta (DLE)."),
        ("lithium", "Posco Holdings",              "PKX",   "NYSE",   "KOR", "Salta",    "Sal de Oro",         "producer",  1,
         "Conglomerado coreano. Proyecto Sal de Oro (Salta)."),
        # --- ORO ---
        ("gold",    "Barrick Gold Corporation",    "GOLD",  "NYSE",   "CAN", "San Juan",  "Veladero",          "miner",     1,
         "Segunda minera de oro del mundo. Opera Veladero (San Juan). Socio en Pascua-Lama."),
        ("gold",    "Newmont Corporation",         "NEM",   "NYSE",   "USA", "Catamarca", "MARA Project",      "miner",     1,
         "Mayor minera de oro del mundo. Proyecto MARA (ex Alumbrera) en Catamarca."),
        ("gold",    "Pan American Silver",         "PAAS",  "NASDAQ", "CAN", "Santa Cruz","Cerro Moro",        "miner",     1,
         "Productor de plata y oro. Opera Cerro Moro en Santa Cruz."),
        ("gold",    "Agnico Eagle Mines",          "AEM",   "NYSE",   "CAN", "Santa Cruz","MARA / Yamana",     "miner",     1,
         "Gran minera canadiense, adquirió Yamana (Santa Cruz)."),
        # --- SOJA ---
        ("soy",     "Bunge Global SA",             "BG",    "NYSE",   "USA", "Santa Fe",  "Complejo Rosario",  "trader",    1,
         "Una de las ABCD. Gran capacidad de crushing en Gran Rosario."),
        ("soy",     "Archer-Daniels-Midland",      "ADM",   "NYSE",   "USA", "Buenos Aires","Complejo Rosario","trader",    1,
         "Una de las ABCD. Fuerte presencia en exportación argentina."),
        ("soy",     "Cargill (privada)",            None,    None,     "USA", "Santa Fe",  "Complejo Rosario",  "trader",    1,
         "Empresa privada, no cotiza. Mayor trader global de granos."),
        ("soy",     "Louis Dreyfus (privada)",      None,    None,     "FRA", "Santa Fe",  "Complejo Rosario",  "trader",    1,
         "Empresa privada. Una de las ABCD. Gran exportadora de soja argentina."),
        ("soy",     "AGD (Aceitera Gral Deheza)",   None,    None,     "ARG", "Córdoba",   "Gral Deheza",       "processor", 1,
         "Empresa nacional. Una de las mayores aceiteras de Argentina. No cotiza."),
        # --- COBRE ---
        ("copper",  "Freeport-McMoRan Inc",         "FCX",   "NYSE",   "USA", None,        None,                "miner",     0,
         "Mayor productor de cobre del mundo. Operaciones en Americas, Africa, Indonesia."),
        ("copper",  "Southern Copper Corporation",  "SCCO",  "NYSE",   "USA", None,        None,                "miner",     0,
         "Principal productor de cobre en América Latina (México, Perú)."),
        ("copper",  "Anglo American plc",           "AAUKF", "OTC",    "GBR", "San Juan",  "Los Sulfatos",      "miner",     1,
         "Conglomerado minero global. Proyecto Los Sulfatos en San Juan (cobre-oro)."),
        ("copper",  "Codelco (estatal)",            None,    None,     "CHL", None,        None,                "miner",     0,
         "Mayor productor mundial de cobre. Empresa estatal chilena, no cotiza."),
        # --- GAS NATURAL ---
        ("natgas",  "YPF S.A.",                     "YPF",   "NYSE",   "ARG", "Neuquén",   "Vaca Muerta",       "producer",  1,
         "Principal empresa de hidrocarburos argentina. Operadora clave de Vaca Muerta (shale gas/oil)."),
        ("natgas",  "Pampa Energía S.A.",            "PAM",   "NYSE",   "ARG", "Neuquén",   "Vaca Muerta",       "producer",  1,
         "Mayor empresa energética privada argentina. Producción gas y generación eléctrica."),
        ("natgas",  "TotalEnergies SE",              "TTE",   "NYSE",   "FRA", "Neuquén",   "Vaca Muerta",       "producer",  1,
         "Multinacional francesa. Operadora de bloques en Vaca Muerta (Fenix, Aguada Pichana)."),
        ("natgas",  "Tecpetrol (Techint)",           None,    None,     "ARG", "Neuquén",   "Fortín de Piedra",  "producer",  1,
         "Empresa del grupo Techint. Operadora de Fortín de Piedra, bloque mayor de Vaca Muerta."),
        # --- TRIGO ---
        ("wheat",   "Bunge Global SA",              "BG",    "NYSE",   "USA", "Santa Fe",  "Complejo Rosario",  "trader",    1,
         "Una de las ABCD. Exportadora y molinera de trigo en Argentina."),
        ("wheat",   "Archer-Daniels-Midland",       "ADM",   "NYSE",   "USA", "Buenos Aires","Complejo Rosario","trader",    1,
         "Una de las ABCD. Exportadora de trigo y harina en Argentina."),
        ("wheat",   "Cargill (privada)",             None,    None,     "USA", "Santa Fe",  "Complejo Rosario",  "trader",    1,
         "Empresa privada. Una de las mayores exportadoras de trigo argentino. No cotiza."),
        ("wheat",   "Cofco International",          None,    None,     "CHN", "Buenos Aires","Complejo Rosario", "trader",    1,
         "Brazo de comercio exterior del estado chino. Gran comprador de trigo y maíz argentino. No cotiza."),
        # --- MAÍZ ---
        ("corn",    "Bunge Global SA",              "BG",    "NYSE",   "USA", "Santa Fe",  "Complejo Rosario",  "trader",    1,
         "Una de las ABCD. Gran capacidad de acopio y exportación de maíz desde el Gran Rosario."),
        ("corn",    "Archer-Daniels-Midland",       "ADM",   "NYSE",   "USA", "Buenos Aires","Complejo Rosario","trader",    1,
         "Una de las ABCD. Fuerte presencia en exportación de maíz argentino."),
        ("corn",    "Cargill (privada)",             None,    None,     "USA", "Santa Fe",  "Complejo Rosario",  "trader",    1,
         "Empresa privada, no cotiza. Mayor exportadora de maíz argentino junto con otras ABCD."),
        ("corn",    "Cofco International",           None,    None,     "CHN", "Buenos Aires","Complejo Rosario", "trader",    1,
         "Brazo de comercio exterior del estado chino. Gran comprador de maíz argentino. No cotiza."),
        ("corn",    "Aceitera Gral Deheza (AGD)",   None,    None,     "ARG", "Córdoba",   "Gral Deheza",       "processor", 1,
         "Empresa nacional. Gran exportadora de maíz y subproductos desde el interior."),
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO companies
            (commodity_id, name, ticker, exchange, country, province_ar,
             project_name, role, is_ar_actor, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, companies)
    print(f"[DB] Empresas: {len(companies)} registros.")


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"[DB] Conectando a: {DB_PATH}")

    with get_conn() as conn:
        init_schema(conn)
        seed_commodities(conn)
        seed_companies(conn)
        conn.commit()

    print("[DB] Inicialización completa.")


if __name__ == "__main__":
    main()
