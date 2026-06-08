# Como Funciona — Documentação Técnica

Guia detalhado da estrutura da tradução para quem deseja contribuir, revisar termos ou adaptar para outros idiomas.

---

## 🧱 Estrutura do jogo

O *Wigmund* utiliza:

- **Engine:** Unreal Engine 4
- **Sistema de textos:** UE4 StringTable (`.uasset` + `.uexp`)
- **Sistema de localização:** UE4 LocRes (`.locres` formato Compact v1)
- **Empacotamento:** PAK v3 com compressão Zlib (blocos de 65536 bytes)

---

## 📁 Arquivos relevantes

Todos os textos do jogo estão dentro do PAK principal:

```
RPG\Content\Paks\pakchunk0-WindowsNoEditor.pak
```

Os arquivos de texto ficam em:

```
RPG/Data/Strings/EN/
  ST_EN_Names.uasset + .uexp      → Itens, armaduras, habilidades, locais
  ST_EN_Common.uasset + .uexp     → Interface, menus, opções, tutoriais
  ST_EN_Quests.uasset + .uexp     → Missões principais e secundárias
  ST_EN_Dialogues.uasset + .uexp  → Diálogos completos

Localization/Game/en/
  Game.locres                     → Menu principal e strings do engine
```

O patch PT-BR (`s_ptbr.pak`) sobrescreve esses arquivos com prioridade sobre o PAK principal, pois o UE4 carrega PAKs em ordem alfabética e o último ganha.

---

## 🗂️ Formato dos arquivos StringTable (.uexp)

Cada `.uexp` de StringTable tem a seguinte estrutura binária:

```
[12 bytes]  Header fixo do UE4 export
[FString]   Nome da tabela (ex: "ST_EN_Names")
[int32]     Número de entradas
Para cada entrada:
  [FString]   Chave (key) — sempre ASCII
  [FString]   Valor (texto) — ASCII ou UTF-16LE
[8 bytes]   Tail fixo (0x00000000 + magic UE4)
```

**FString encoding no UE4:**
- `slen > 0`: string em UTF-8/ASCII, comprimento inclui o `\0`
- `slen < 0`: string em UTF-16LE, `abs(slen)` = número de chars incluindo `\0`

**Regra crítica:** strings com qualquer caractere não-ASCII (ã, ç, á, etc.) DEVEM usar UTF-16LE (slen negativo). Usar UTF-8 para acentos causa exibição incorreta no engine.

---

## 🗂️ Formato do Game.locres (Compact v1)

```
[16 bytes]  GUID do pacote
[1 byte]    Versão (1 = Compact)
[8 bytes]   int64: offset do array de strings
[25+]       Seção de namespaces/chaves:
              [int32] namespace count
              Para cada namespace:
                [FString] nome do namespace
                [int32] entry count
                Para cada entry:
                  [FString] chave GUID
                  [uint32]  key hash
                  [int32]   índice no array de strings
[str_off]   Array de strings:
              [int32] string count
              [FString × N] strings localizadas
```

**Atenção:** o `string_array_offset` deve apontar exatamente para o início do array de strings. Um valor errado trava o jogo na inicialização sem gerar log.

---

## 🔧 O .uasset e o SerialSize

O `.uasset` de cada StringTable contém no ExportMap um campo `SerialSize` (int64) que armazena `tamanho_do_uexp - 4`. Quando o `.uexp` muda de tamanho (pela tradução), esse campo deve ser atualizado — caso contrário o engine crasha ao tentar ler o arquivo.

O script `build_ptbr_pak.py` detecta e atualiza esse campo automaticamente.

---

## 📦 Estrutura do PAK

O PAK do Wigmund usa o formato UE4 PAK v3:

```
[corpo]  Para cada arquivo:
           Header da entrada (48 + 4 + n_blocos×16 + 5 bytes)
           Dados comprimidos (Zlib, blocos de 65536 bytes)
[índice] Mount point + lista de entradas com metadados
[footer] Magic(4) + Version(4) + IndexOffset(8) + IndexSize(8) + SHA1(20)
```

**SHA1:** calculado sobre os dados **descomprimidos** de cada arquivo, e também sobre o índice completo.

---

## 🛠️ Scripts do projeto

| Script | Função |
|---|---|
| `extrair_wigmund.py` | Extrai os 8 arquivos de StringTable do pakchunk0 |
| `extrair_uitooltip.py` | Extrai o UI_Tooltip Blueprint do pakchunk0 |
| `extrair_fonte.py` | Extrai as fontes TTF do pakchunk0 |
| `build_ptbr_pak.py` | Gera o s_ptbr.pak completo com todas as traduções |

---

## 🤝 Como contribuir

1. Faça fork do repositório
2. Edite o arquivo `wigmund_traducao_EN.csv`:
   ```
   categoria,chave,ingles,russo,portugues
   Dialogues,c1_narr1,"Como durante um eclipse...","Как во время...","Sua tradução aqui"
   ```
3. Rode o script de build:
   ```
   python build_ptbr_pak.py
   ```
4. Teste o `s_ptbr.pak` gerado no jogo
5. Abra um Pull Request

---

## 📌 Descobertas técnicas importantes

Durante o desenvolvimento foram feitas as seguintes descobertas:

- **UTF-16LE obrigatório:** acentos em UTF-8 causam `?` na tela — o engine não interpreta multibyte em FStrings de textos de UI
- **SerialSize:** deve ser atualizado no `.uasset` quando o `.uexp` muda de tamanho
- **Compressão Zlib:** o PAK deve usar Zlib com blocos de 65536 bytes — PAKs sem compressão causam travamento silencioso do processo para arquivos Blueprint
- **string_array_offset do locres:** um valor errado trava o jogo antes de criar o arquivo de log
- **Locres do pakchunk0:** o arquivo já continha textos em russo (patch russo havia sido instalado anteriormente), não inglês — foi necessário fazer mapeamento direto russo→PT-BR para as strings do menu principal
- **UI_Tooltip Blueprint:** strings hardcoded no bytecode UE4 seguem o padrão `0x1F + string_ascii + 0x00 + 0x0F + id` — substituição in-place requer tamanho exato em bytes

---

## 📌 Histórico de versões

- **1.0.0 — Jun/2026**
  - Primeira versão pública
  - 2.178 termos traduzidos nas StringTables
  - ~700 strings do locres traduzidas (menu principal + UI do engine)
