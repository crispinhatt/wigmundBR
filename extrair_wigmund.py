"""
Extrator de StringTables do Wigmund
Extrai os 4 arquivos .uexp de texto do pakchunk0-WindowsNoEditor.pak
Sem dependencias externas - usa apenas a biblioteca padrao do Python 3
"""

import struct
import zlib
import os
import sys

# ── Arquivos alvo ─────────────────────────────────────────────────────────────
TARGET_FILES = [
    "RPG/Data/Strings/EN/ST_EN_Common.uexp",
    "RPG/Data/Strings/EN/ST_EN_Dialogues.uexp",
    "RPG/Data/Strings/EN/ST_EN_Names.uexp",
    "RPG/Data/Strings/EN/ST_EN_Quests.uexp",
    # .uasset companions (necessarios para o UE4 carregar os .uexp)
    "RPG/Data/Strings/EN/ST_EN_Common.uasset",
    "RPG/Data/Strings/EN/ST_EN_Dialogues.uasset",
    "RPG/Data/Strings/EN/ST_EN_Names.uasset",
    "RPG/Data/Strings/EN/ST_EN_Quests.uasset",
]

PAK_MAGIC = 0x5A6F12E1

# ── Leitura de FString ────────────────────────────────────────────────────────
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

# ── Parser do indice do PAK ───────────────────────────────────────────────────
def parse_pak_index(f):
    f.seek(-44, 2)
    footer = f.read(44)
    magic   = struct.unpack_from('<I', footer, 0)[0]
    version = struct.unpack_from('<I', footer, 4)[0]
    idx_off = struct.unpack_from('<Q', footer, 8)[0]
    idx_sz  = struct.unpack_from('<Q', footer, 16)[0]

    if magic != PAK_MAGIC:
        raise ValueError(f"Magic invalido: 0x{magic:08X} (esperado 0x{PAK_MAGIC:08X})")

    print(f"  PAK versao {version}, indice @ offset {idx_off} ({idx_sz} bytes)")

    f.seek(idx_off)
    idx = f.read(idx_sz)

    mount_point, offset = read_fstring(idx, 0)
    file_count = struct.unpack_from('<i', idx, offset)[0]
    offset += 4
    print(f"  Mount point: {mount_point!r}  |  {file_count} arquivos no indice")

    entries = {}
    for _ in range(file_count):
        filename, offset = read_fstring(idx, offset)

        entry_offset = struct.unpack_from('<Q', idx, offset)[0]; offset += 8
        size_comp    = struct.unpack_from('<Q', idx, offset)[0]; offset += 8
        size_uncomp  = struct.unpack_from('<Q', idx, offset)[0]; offset += 8
        comp_method  = struct.unpack_from('<I', idx, offset)[0]; offset += 4
        offset += 20  # SHA1

        blocks = []
        if comp_method != 0:
            block_count = struct.unpack_from('<I', idx, offset)[0]; offset += 4
            for _ in range(block_count):
                bs = struct.unpack_from('<Q', idx, offset)[0]; offset += 8
                be = struct.unpack_from('<Q', idx, offset)[0]; offset += 8
                blocks.append((bs, be))

        offset += 1  # flags
        block_size = struct.unpack_from('<I', idx, offset)[0]; offset += 4

        entries[filename] = {
            'offset':      entry_offset,
            'compressed':  size_comp,
            'uncompressed': size_uncomp,
            'method':      comp_method,
            'blocks':      blocks,
        }

    return entries, version

# ── Calcula tamanho do header in-file de uma entrada ─────────────────────────
def entry_header_size(method, blocks):
    size = 48  # offset(8)+comp(8)+uncomp(8)+method(4)+sha1(20)
    if method != 0:
        size += 4 + len(blocks) * 16
    size += 5   # flags(1)+block_size(4)
    return size

# ── Extrai e descomprime um arquivo ──────────────────────────────────────────
def extract_entry(f, entry):
    method  = entry['method']
    blocks  = entry['blocks']
    hdr_sz  = entry_header_size(method, blocks)

    if method == 0:  # sem compressao
        f.seek(entry['offset'] + hdr_sz)
        return f.read(entry['uncompressed'])

    elif method == 1:  # Zlib
        result = b''
        for b_start, b_end in blocks:
            f.seek(b_start)
            result += zlib.decompress(f.read(b_end - b_start))
        return result

    else:
        raise NotImplementedError(f"Metodo de compressao nao suportado: {method}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Localizar o pakchunk0
    default_pak = r"I:\STEAMLIBRARY\STEAMAPPS\COMMON\WIGMUND\RPG\Content\Paks\pakchunk0-WindowsNoEditor.pak"

    if len(sys.argv) > 1:
        pak_path = sys.argv[1]
    elif os.path.exists(default_pak):
        pak_path = default_pak
    else:
        print("Uso: python extrair_wigmund.py [caminho_para_pakchunk0.pak]")
        print(f"Caminho padrao nao encontrado: {default_pak}")
        sys.exit(1)

    if not os.path.exists(pak_path):
        print(f"Arquivo nao encontrado: {pak_path}")
        sys.exit(1)

    print(f"\nLendo: {pak_path}")
    print(f"Tamanho: {os.path.getsize(pak_path):,} bytes\n")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wigmund_strings_EN")

    with open(pak_path, 'rb') as f:
        entries, version = parse_pak_index(f)

        print(f"\nProcurando os {len(TARGET_FILES)} arquivos alvo...\n")
        found = 0

        for target in TARGET_FILES:
            # O mount point e "../../../" entao a chave no indice pode ter prefixo variavel
            # Tentar correspondencia pelo sufixo
            matched_key = None
            for key in entries:
                if key.replace('\\', '/').endswith(target.replace('\\', '/')):
                    matched_key = key
                    break

            if matched_key is None:
                print(f"  [NAO ENCONTRADO] {target}")
                continue

            entry = entries[matched_key]
            data  = extract_entry(f, entry)

            out_path = os.path.join(out_dir, target.replace('/', os.sep))
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, 'wb') as out:
                out.write(data)

            print(f"  [OK] {target}")
            print(f"       {entry['uncompressed']:,} bytes  (comprimido: {entry['compressed']:,})")
            found += 1

    print(f"\n{'='*50}")
    print(f"Extraidos: {found}/{len(TARGET_FILES)} arquivos")
    print(f"Pasta de saida: {out_dir}")

    if found > 0:
        print("\nEnvie a pasta 'wigmund_strings_EN' completa para o Claude.")

if __name__ == '__main__':
    main()
