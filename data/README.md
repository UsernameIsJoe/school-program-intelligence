# Component fixtures

| Path | Component |
|------|-----------|
| [`a_program/`](a_program/) | A — programs, relationships, schedule |
| [`b_spatial/`](b_spatial/) | B — floor plan + space attributes |
| [`c_preferences/`](c_preferences/) | C — prompt + default weights |
| [`assignments/`](assignments/) | Test assignments for engine/rating only |

```bash
spi a --fixture toy_elementary
spi b --fixture toy_elementary
spi c --fixture toy_elementary
spi engine --fixture toy_elementary --assignment A
spi rating --fixture toy_elementary --assignment A
```
