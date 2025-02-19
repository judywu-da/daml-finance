# Style Guide

This style guide details the formatting and styling of Daml and client-side code that is contained within this repository.

## Daml

### Spacing

- Use 2 spaces for indentation
- Use single empty line to separate sections (and end the file with a single empty line)
- [*decide*] Use at most 100 characters per line (alt. toggle text wrap in vscode)

### Imports

- Order imports alphabetically with upper-case before lower-case:

  ```haskell
  import DA.Set (empty)
  import Daml.Script
  ```

- Use explicit imports and order them alphabetically ordered:

  ```haskell
  import DA.Set (empty, fromList, singleton)
  ```

- Use qualified imports for interface modules:

  ```haskell
  import Daml.Finance.Interface.Asset.Holding qualified as Holding (view, I, V)
  ```

### Module structure

- Modules use the following newlines:

  ```haskell
  module Foo.Bar where

  import A.B.C
  import A.B.D

  template Baz
    with
      ...

  template Baz2
    with
      ...
    ```

### Template structure

- Templates use the following indentation and newlines:

  ```haskell
  template Foo
    with
      party1 : Party
      party2 : Party
    where
      signatory party1
      observer party2

      key party1 : Party
      maintainer party1

    choice Delete : ()
      with
        party : Party
      controller party
      do
        pure ()
  ```

### Interface structure

- Group all serializable interface fields into a `View` type:

  ```haskell
  data View = View
    with
      custodian : Party
        -- ^ Party providing accounting services.
      id : Text
        -- ^ Textual description of the account.
      owner : Party
        -- ^ Party owning this account.
    deriving (Eq, Ord, Show)
  ```

- Add a `viewtype` definition to the interface with the `View` type:

  ```haskell
  interface Account where
    viewtype View
    ...
  ```

- Define `I` and `V` type aliases for the interface resp. view type:

  ```haskell
  type I = Account
  type V = View
  ```

- Use qualified imports `I` and `V` to refer to interface resp. view types in consuming code:

  ```haskell
  let iCid : ContractId Holding.I = ...
  let iView : Holding.V = ...
  ```

- For interface choices with empty implemenations

To prevent us from keeping the implementation arguments 'in sync' with the choice arguments, we use

```haskell
foo : Foo -> Update res
choice Foo : res
  with
    a : A
    b : B
  controller actor
  do
    foo this arg
```

instead of

```haskell
foo : arg1 -> arg2 -> Update res
choice Foo : res
  with
    a : A
    b : B
  controller actor
  do
    foo this a b
```

Recall that `arg` is syntactic sugar for `Foo with a; b` when used in the body of the choice.

### `do` notation

- Place the main `do` in a choice on its own line:

  ```haskell
  choice Delete : ()
    controller party
    do
      pure ()
  ```

- Place `do` in functions and expressions on the same line:

  ```haskell
  let
    foo = do
      if a
      then do
        ...
      else do
        ...
  ```

### `let` bindings

- Single-line body:

  ```haskell
  let a = b
  ```

- Multi-line body:

  ```haskell
  let
    a =
      if b
      then c
      else d
  ```

- Multiple bindings:

  ```haskell
  let
    a = b
    c = d
  ```

### Functions

- Add function type signatures to all top-level functions:

  ```haskell
  add : Decimal -> Decimal -> Decimal
  add a b = a + b
  ```

- Don't add type signatures for functions in `let` bindings (unless you think it is necessary):

  ```haskell
  let add a b = a + b
  ```

- Use `pure` instead of `pure` as more idiomatic

### Constructors

- Use `;` to separate parameters to differentiate from list and tuple separators:

  ```haskell
  let foo = Foo with a = b; c = [d, e]; f = (g, h)
  ```

- Use short-hand parameter notation:

  ```haskell
  let foo = Foo with a; b; c
  ```

- Don't use `..` as it makes code harder to understand (and might cause bugs in case of code changes)
- Don't use positional constructors as they are harder to read (and might cause bugs in case of code changes)

## Javascript / Typescript

`TODO`
