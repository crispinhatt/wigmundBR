# Wigmund — Tradução PT-BR

> Tradução não-oficial completa do jogo para o Português do Brasil.

---

## 📋 Sobre o projeto

Este projeto assim como sua documentação foram feitos inteiramente com o uso da plataforma CLAUDE, sendo apenas alguns poucos termos revisados manualmente.

Este projeto traduz **2.178 termos** do jogo Wigmund para o Português do Brasil, cobrindo todos os textos visíveis do jogo:

- Diálogos e narrativa completa da história (5 capítulos)
- Missões principais e secundárias
- Interface (menus, HUD, botões, opções)
- Itens, armaduras, armas e habilidades
- NPCs, locais e pontos de interesse
- Sistema de profissões e receitas
- Tutoriais e notificações

**Versão do jogo testada:** 1.4.7
**Plataforma:** PC (Steam)

---

## ✅ O que foi traduzido

| Categoria | Termos | Descrição |
|---|---|---|
| ST_EN_Names | 751 | Itens, armaduras, armas, habilidades, locais, NPCs |
| ST_EN_Dialogues | 777 | Diálogos completos dos 5 capítulos |
| ST_EN_Quests | 370 | Missões principais e secundárias |
| ST_EN_Common | 280 | Interface, menus, opções, tutoriais |
| Game.locres | ~700 | Menu principal, UI do engine, strings do sistema |

### Nomes próprios mantidos em inglês (intencionalmente)
Nomes de personagens e locais do universo do jogo foram preservados no idioma original:
`Wigmund`, `Wigstan`, `Cyneric`, `Modig`, `Arael`, `Raedan`, `Alfred`, `Antiochus`, `Aefestra`, `Naegling`, `Ashdown`, `Clwyd`

---

## Como foi traduzido?

Para saber mais detalhes leia `COMO_FUNCIONA.md`

Com ajuda da CLAUDE foi verificado que os textos estavam armazenados em arquivos `.uexp` de StringTable dentro do `pakchunk0-WindowsNoEditor.pak` (formato Unreal Engine 4).

CLAUDE criou um script Python (`extrair_wigmund.py`) para extrair os 8 arquivos de texto do PAK principal. Os textos originais em inglês (versão 1.4.7) foram extraídos como fonte de verdade — o patch russo existente (v1.4.5) foi usado apenas como referência de estrutura.

CLAUDE realizou a tradução de todas as 2.178 strings diretamente, respeitando o tom medieval do jogo, mantendo nomes próprios e preservando variáveis dinâmicas como `{0}`, `{b.Effect1Value}`, `\r\n` etc.

Por fim, CLAUDE criou o script `build_ptbr_pak.py` que injeta as traduções nos arquivos binários UE4 (formato FString UTF-16LE para caracteres acentuados), atualiza os metadados do `.uasset` e empacota tudo num novo `s_ptbr.pak` com compressão Zlib — idêntico em estrutura ao patch russo oficial de referência.

---

## 🛠️ Como instalar

### Pré-requisitos
- Jogo Wigmund instalado via Steam
- O arquivo `s_ptbr.pak` (disponível em [Releases](../../releases))

### Passo a passo

**1. Baixe o arquivo de tradução**

Acesse a seção [Releases](../../releases) deste repositório e baixe o arquivo `s_ptbr.pak`.

**2. Localize a pasta do jogo**

```
<Steam>\steamapps\common\Wigmund\RPG\Content\Paks\
```

Substitua `<Steam>` pelo caminho da sua biblioteca Steam (ex: `I:\SteamLibrary`).

**3. Copie o arquivo**

Cole o `s_ptbr.pak` dentro da pasta `Paks\`. A pasta deve ficar assim:

```
Paks\
  pakchunk0-WindowsNoEditor.pak   ← original do jogo, não mexa
  s_ptbr.pak                      ← tradução PT-BR
```

**4. Jogue!**

Abra o jogo normalmente pelo Steam. Os textos aparecerão em **Português do Brasil** automaticamente.

> ⚠️ Se você tinha o patch russo instalado (`s_rus.pak` e `s_fonts.pak`), **remova-os** antes de instalar o PT-BR.

---

## 🔄 Como desinstalar

Para voltar ao inglês original:

1. Feche o jogo
2. Delete o arquivo `s_ptbr.pak` da pasta `Paks\`
3. Abra o jogo normalmente

---

## ⚠️ Avisos

- Esta é uma tradução **não-oficial** — não tem relação com os desenvolvedores do Wigmund
- Testada na versão **1.4.7** — pode ser necessário reaplicar após atualizações do jogo
- Se o jogo atualizar e a tradução parar de funcionar, remova o `s_ptbr.pak` e aguarde uma atualização deste projeto
- Algumas strings de UI do Blueprint (`Shield`, `Axe`, `1H Weapon` etc.) estão em inglês — são hardcoded no engine e requerem engenharia reversa mais complexa de Blueprint compilado para serem traduzidas

---

## 🐛 Reportar erros

Encontrou um erro de tradução, texto cortado ou algo que não faz sentido em PT-BR? Abra uma [Issue](../../issues) com:

- Print da tela com o erro
- Contexto (qual missão, menu, personagem)
- Sugestão de tradução correta (opcional)

---

## 🔧 Para desenvolvedores

Quer contribuir com melhorias ou criar uma tradução para outro idioma? Veja o arquivo [COMO_FUNCIONA.md](COMO_FUNCIONA.md) para entender a estrutura técnica do projeto.

---

## 📜 Licença

Este projeto está licenciado sob a MIT License.

Você pode usar, modificar e distribuir este projeto livremente.

Wigmund © seus respectivos desenvolvedores. Este projeto é uma tradução não-oficial e não possui vínculo com os detentores da propriedade intelectual.
