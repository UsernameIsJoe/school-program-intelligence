# Component build plan

School Program Intelligence is developed **component-by-component**:

```text
A  a_program        programs · relationships · schedule/time
B  b_spatial        floor plan · capacity · dimensions · circulation
C  c_preferences    prompt → editable priority weights
   engine           simulate one assignment against A+B → metrics
   rating           apply C weights to metrics → score
```

Full search / populate / studio Run is **deferred** until A, B, C, engine, and rating are each clear and tested.

## Package map

```text
src/school_program_intelligence/
  a_program/
  b_spatial/
  c_preferences/
  engine/
  rating/
  shared/
  cli.py
```

## Data

```text
data/a_program/toy_elementary/
data/b_spatial/toy_elementary/
data/c_preferences/toy_elementary/
data/assignments/toy_elementary/   # engine/rating test maps only
```

## CLI (inspect only)

```bash
spi a --fixture toy_elementary
spi b --fixture toy_elementary
spi c --fixture toy_elementary
spi engine --assignment A --diagnose
spi rating --assignment A
```

## Order of work

1. Prove **A** (model + inspect + tests)
2. Prove **B**
3. Prove **C**
4. Prove **engine** (metrics, no ranking)
5. Prove **rating** (weights change scores predictably)
6. Only then: populate candidates / UI

## Locked decisions

1. Public repo `UsernameIsJoe/school-program-intelligence`
2. MIT
3. Engines measure; C only sets weights
4. No dual legacy packages (`evaluation`, `optimization`, `pipeline`, all-in-one studio)
