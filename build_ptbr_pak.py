"""
build_ptbr_pak.py  v2
Gera s_ptbr.pak com as traducoes PT-BR do Wigmund.
Sem dependencias externas — apenas Python 3 padrao.

Uso:
  python build_ptbr_pak.py

Saida:
  s_ptbr.pak  (mesmo diretorio do script)

Instalacao:
  Copie s_ptbr.pak para:
  <Steam>\steamapps\common\Wigmund\RPG\Content\Paks\
"""

import struct, json, hashlib, os, sys, csv, zlib

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(SCRIPT_DIR, 'wigmund_strings_EN', 'RPG', 'Data', 'Strings', 'EN')
CSV_PATH    = os.path.join(SCRIPT_DIR, 'wigmund_traducao_EN.csv')
OUTPUT_PAK  = os.path.join(SCRIPT_DIR, 's_ptbr.pak')

PAK_MAGIC   = 0x5A6F12E1
PAK_VERSION = 3
MOUNT_POINT = '../../../RPG/Content/'
BLOCK_SIZE  = 65536

# ── FString helpers ───────────────────────────────────────────────────────────
def encode_fstring(s):
    """
    FString UE4:
    - ASCII puro: slen positivo + bytes + null
    - Com chars nao-ASCII: slen negativo + UTF-16LE + null null
    """
    if not s:
        return struct.pack('<i', 0)
    if all(ord(c) < 128 for c in s):
        enc = s.encode('ascii') + b'\x00'
        return struct.pack('<i', len(enc)) + enc
    else:
        enc = s.encode('utf-16-le') + b'\x00\x00'
        return struct.pack('<i', -(len(s) + 1)) + enc

def encode_fstring_utf8(s):
    if not s: return struct.pack('<i', 0)
    enc = s.encode('utf-8') + b'\x00'
    return struct.pack('<i', len(enc)) + enc

def read_fstring(data, offset):
    slen = struct.unpack_from('<i', data, offset)[0]
    offset += 4
    if slen == 0:
        return '', offset
    if slen > 0:
        s = data[offset:offset+slen].decode('utf-8', errors='replace').rstrip('\x00')
        return s, offset + slen
    else:
        n = -slen
        s = data[offset:offset+n*2].decode('utf-16-le', errors='replace').rstrip('\x00')
        return s, offset + n*2

# ── Carregar CSV ──────────────────────────────────────────────────────────────
def load_csv(path):
    result = {}
    with open(path, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            result.setdefault(row['categoria'], {})[row['chave']] = row['portugues']
    return result

# ── Reconstruir .uexp ─────────────────────────────────────────────────────────
def rebuild_uexp(original_path, translations, cat_name):
    with open(original_path, 'rb') as f:
        data = f.read()

    table_name, offset_after_name = read_fstring(data, 12)
    entry_count = struct.unpack_from('<i', data, offset_after_name)[0]
    header_end  = offset_after_name + 4

    out = bytearray(data[:header_end])
    offset = header_end
    replaced = 0

    for _ in range(entry_count):
        key,  offset = read_fstring(data, offset)
        orig, offset = read_fstring(data, offset)
        pt = translations.get(key, '') or orig
        if pt != orig:
            replaced += 1
        out += encode_fstring(key)
        out += encode_fstring(pt)

    # Tail fixo (4 bytes zeros + 4 bytes magic do UE4)
    out += data[offset:]

    print(f"  {cat_name}: {entry_count} entradas, {replaced} traduzidas, "
          f"{len(data)} -> {len(out)} bytes")
    return bytes(out)

# ── Atualizar SerialSize no .uasset ───────────────────────────────────────────
def patch_uasset(uasset_path, old_uexp_size, new_uexp_size):
    """
    O ExportMap do .uasset contem SerialSize (int64) = tamanho do .uexp - 4.
    Localiza esse valor e atualiza para o novo tamanho.
    """
    with open(uasset_path, 'rb') as f:
        data = bytearray(f.read())

    old_serial = old_uexp_size - 4
    new_serial = new_uexp_size - 4

    needle = struct.pack('<q', old_serial)
    pos = data.find(needle)

    if pos == -1:
        # Tentar int32
        needle32 = struct.pack('<i', old_serial)
        pos32 = data.find(needle32)
        if pos32 != -1 and data[pos32+4:pos32+8] == b'\x00\x00\x00\x00':
            pos = pos32
        else:
            print(f"  AVISO: SerialSize nao encontrado no .uasset — usando original")
            return bytes(data)

    struct.pack_into('<q', data, pos, new_serial)
    print(f"  .uasset: SerialSize atualizado {old_serial} -> {new_serial} @ offset {pos}")
    return bytes(data)

# ── SHA1 ──────────────────────────────────────────────────────────────────────
def sha1(data):
    return hashlib.sha1(data).digest()

# ── Comprimir com Zlib em blocos ──────────────────────────────────────────────
def compress_blocks(data):
    blocks_rel = []
    parts = []
    cur = 0
    for i in range(0, len(data), BLOCK_SIZE):
        chunk = data[i:i+BLOCK_SIZE]
        comp  = zlib.compress(chunk, 6)
        blocks_rel.append((cur, cur + len(comp)))
        parts.append(comp)
        cur += len(comp)
    return blocks_rel, b''.join(parts)

# ── Montar PAK com Zlib ───────────────────────────────────────────────────────
def build_pak(files):
    """files: [(virtual_path, bytes)]"""

    # Comprimir e calcular offsets
    entries = []
    cur_offset = 0
    for vpath, raw in files:
        blocks_rel, comp = compress_blocks(raw)
        n_blocks = len(blocks_rel)
        hdr_sz   = 48 + 4 + n_blocks * 16 + 5
        data_start = cur_offset + hdr_sz
        blocks_abs = [(data_start + bs, data_start + be) for bs, be in blocks_rel]
        entries.append({
            'vpath':      vpath,
            'raw':        raw,
            'comp':       comp,
            'blocks_abs': blocks_abs,
            'pak_offset': cur_offset,
        })
        cur_offset += hdr_sz + len(comp)

    index_offset = cur_offset

    # Corpo
    body = bytearray()
    for e in entries:
        hdr  = struct.pack('<Q', e['pak_offset'])
        hdr += struct.pack('<Q', len(e['comp']))
        hdr += struct.pack('<Q', len(e['raw']))
        hdr += struct.pack('<I', 1)              # Zlib
        hdr += sha1(e['raw'])
        hdr += struct.pack('<I', len(e['blocks_abs']))
        for bs, be in e['blocks_abs']:
            hdr += struct.pack('<Q', bs)
            hdr += struct.pack('<Q', be)
        hdr += struct.pack('<B', 0)
        hdr += struct.pack('<I', BLOCK_SIZE)
        body += hdr + e['comp']

    # Indice
    idx = bytearray()
    idx += encode_fstring_utf8(MOUNT_POINT)
    idx += struct.pack('<i', len(entries))
    for e in entries:
        idx += encode_fstring_utf8(e['vpath'])
        hdr  = struct.pack('<Q', e['pak_offset'])
        hdr += struct.pack('<Q', len(e['comp']))
        hdr += struct.pack('<Q', len(e['raw']))
        hdr += struct.pack('<I', 1)
        hdr += sha1(e['raw'])
        hdr += struct.pack('<I', len(e['blocks_abs']))
        for bs, be in e['blocks_abs']:
            hdr += struct.pack('<Q', bs)
            hdr += struct.pack('<Q', be)
        hdr += struct.pack('<B', 0)
        hdr += struct.pack('<I', BLOCK_SIZE)
        idx += hdr

    idx_bytes = bytes(idx)

    # Footer
    footer  = struct.pack('<I', PAK_MAGIC)
    footer += struct.pack('<I', PAK_VERSION)
    footer += struct.pack('<Q', index_offset)
    footer += struct.pack('<Q', len(idx_bytes))
    footer += sha1(idx_bytes)

    return bytes(body) + idx_bytes + footer

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Wigmund PT-BR PAK Builder v2")
    print("=" * 55)

    for path, label in [(CSV_PATH, 'CSV'), (UPLOADS_DIR, 'pasta de originais')]:
        if not os.path.exists(path):
            print(f"\nERRO: {label} nao encontrado:\n  {path}")
            sys.exit(1)

    print(f"\nCarregando traducoes...")
    translations = load_csv(CSV_PATH)
    total = sum(len(v) for v in translations.values())
    print(f"  {total} strings")

    cat_map = [
        ('Names',     'ST_EN_Names'),
        ('Common',    'ST_EN_Common'),
        ('Quests',    'ST_EN_Quests'),
        ('Dialogues', 'ST_EN_Dialogues'),
    ]

    # Incluir arquivos extras se existirem
    locres_path    = os.path.join(SCRIPT_DIR, 'Game_ptbr.locres')
    ui_uexp_path   = os.path.join(SCRIPT_DIR, 'UI_Tooltip_ptbr.uexp')
    ui_uasset_path = os.path.join(SCRIPT_DIR, 'wigmund_ui',
                                  'RPG', 'Blueprints', 'UI', 'Game', 'UI_Tooltip.uasset')
    ui_uexp_orig   = os.path.join(SCRIPT_DIR, 'wigmund_ui',
                                  'RPG', 'Blueprints', 'UI', 'Game', 'UI_Tooltip.uexp')

    print("\nReconstruindo arquivos...")
    pak_files = []

    for cat, base in cat_map:
        uexp_path   = os.path.join(UPLOADS_DIR, f'{base}.uexp')
        uasset_path = os.path.join(UPLOADS_DIR, f'{base}.uasset')

        if not os.path.exists(uexp_path) or not os.path.exists(uasset_path):
            print(f"  AVISO: {base} nao encontrado, pulando.")
            continue

        old_uexp_size = os.path.getsize(uexp_path)
        new_uexp   = rebuild_uexp(uexp_path, translations.get(cat, {}), cat)
        new_uasset = patch_uasset(uasset_path, old_uexp_size, len(new_uexp))

        vbase = f'RPG/Data/Strings/EN/{base}'
        pak_files.append((f'{vbase}.uasset', new_uasset))
        pak_files.append((f'{vbase}.uexp',   new_uexp))

    # Game.locres
    if os.path.exists(locres_path):
        with open(locres_path, 'rb') as f:
            pak_files.append(('Localization/Game/en/Game.locres', f.read()))
        print(f"  Locres PT-BR incluido")
    else:
        print("  AVISO: Game_ptbr.locres nao encontrado, pulando.")

    # UI_Tooltip
    if os.path.exists(ui_uexp_path) and os.path.exists(ui_uasset_path):
        with open(ui_uasset_path, 'rb') as f: uasset_data = f.read()
        with open(ui_uexp_path,   'rb') as f: uexp_data   = f.read()
        with open(ui_uexp_orig,   'rb') as f: uexp_bak    = f.read() if os.path.exists(ui_uexp_orig) else uexp_data

        pak_files.append(('RPG/Blueprints/UI/Game/UI_Tooltip.uasset',     uasset_data))
        pak_files.append(('RPG/Blueprints/UI/Game/UI_Tooltip.uasset.bak', uasset_data))
        pak_files.append(('RPG/Blueprints/UI/Game/UI_Tooltip.uexp',       uexp_data))
        pak_files.append(('RPG/Blueprints/UI/Game/UI_Tooltip.uexp.bak',   uexp_bak))
        print(f"  UI_Tooltip incluido ({len(uexp_data):,} bytes)")
    else:
        print("  AVISO: UI_Tooltip nao encontrado, pulando.")

    if not pak_files:
        print("\nNenhum arquivo processado. Abortando.")
        sys.exit(1)

    print(f"\nEmpacotando {len(pak_files)} arquivos (Zlib)...")
    pak_data = build_pak(pak_files)

    with open(OUTPUT_PAK, 'wb') as f:
        f.write(pak_data)

    print(f"\nPAK gerado com sucesso!")
    print(f"  Arquivo : {OUTPUT_PAK}")
    print(f"  Tamanho : {len(pak_data)/1024:.1f} KB")
    print()
    print("=" * 55)
    print("  INSTALACAO:")
    print("  Copie s_ptbr.pak para:")
    print(r"  <Steam>\steamapps\common\Wigmund\RPG\Content\Paks\ ")
    print("=" * 55)

if __name__ == '__main__':
    main()
