# Bundled fonts

Materializr ships these TrueType fonts for the sketch **Text** tool, plus two
faces that are UI-only and are merged into the ImGui font atlas instead. All are
free/redistributable; full license texts are in `licenses/`. Copyright notices
are preserved below as required by their licenses.

| Family (picker name) | File | Copyright | License |
|---|---|---|---|
| Mono (JetBrains) | `JetBrainsMono-Regular.ttf` | © JetBrains s.r.o. | SIL OFL 1.1 |
| Sans (DejaVu) | `DejaVuSans.ttf` | Bitstream Vera / Arev fonts © Bitstream Inc., Tavmjong Bah | Bitstream Vera + Arev (permissive) |
| Serif (DejaVu) | `DejaVuSerif.ttf` | Bitstream Vera / Arev fonts © Bitstream Inc., Tavmjong Bah | Bitstream Vera + Arev (permissive) |
| Times (Liberation) | `LiberationSerif-Regular.ttf` | © Red Hat, Inc. | SIL OFL 1.1 |
| Arial (Liberation) | `LiberationSans-Regular.ttf` | © Red Hat, Inc. | SIL OFL 1.1 |
| Ubuntu | `Ubuntu-Regular.ttf` | © Canonical Ltd. | Ubuntu Font Licence 1.0 |
| Comic (Neue) | `ComicNeue-Regular.ttf` | © The Comic Neue Project Authors | SIL OFL 1.1 |
| Stencil (Black Ops) | `BlackOpsOne-Regular.ttf` | © The Black Ops One Project Authors (Matt McInerney) | SIL OFL 1.1 |
| Impact (Anton) | `Anton-Regular.ttf` | © The Anton Project Authors (Vernon Adams) | SIL OFL 1.1 |
| Script (Pacifico) | `Pacifico-Regular.ttf` | © The Pacifico Project Authors (Vernon Adams) | SIL OFL 1.1 |
| *(UI icons - not in the Text picker)* | `Iconoir.ttf` | Iconoir © Luca Burgio; font build © Silbad (iconoir-font) | MIT |
| *(UI text - not in the Text picker)* | `NotoSansSC-Regular.ttf` | © 2014-2021 Adobe, with Reserved Font Name 'Source' (Noto Sans SC); GB2312 subset built for Materializr | SIL OFL 1.1 |

License texts in `licenses/`:
- `OFL-1.1.txt` - SIL Open Font License 1.1 (JetBrains Mono, Liberation, Comic Neue, Black Ops One, Anton, Pacifico, Noto Sans SC).
- `UFL-1.0.txt` - Ubuntu Font Licence 1.0 (Ubuntu).
- `DejaVu-copyright.txt` - Bitstream Vera + Arev (DejaVu).
- `Liberation-copyright.txt` - distribution copyright/license for the Liberation family.
- `Iconoir-LICENSE.txt` - MIT (Iconoir icon glyph font; used by the im-touch UI shell, merged into the ImGui atlas - deliberately NOT offered by the Text tool).

Liberation Serif and Liberation Sans are *metrically compatible* with Times New
Roman and Arial respectively (matching widths and shapes); the real Microsoft
fonts are proprietary and are NOT bundled.

Liberation 2.x is distributed under the SIL OFL 1.1; see `Liberation-copyright.txt`.

The Noto Sans SC file is a **subset**: the variable Noto Sans SC instance at
weight 400, cut down to the GB2312 hanzi set (6763 characters) plus ASCII,
Latin-1, general punctuation, CJK punctuation and the halfwidth/fullwidth forms.
It carries the CJK glyphs the Chinese interface needs; English and the western
languages keep using JetBrains Mono, which is merged first. Subsetting is a
modification under the OFL, so the name is 'Noto Sans SC' rather than the
Reserved Font Name 'Source'; the OFL permits that, and the original copyright
and license above are unchanged.
