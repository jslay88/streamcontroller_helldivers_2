# HELLDIVERS 2 [StreamController](https://github.com/StreamController/StreamController) Plugin

Assumes the following:

- Left Control will open Stratagem menu (Hold/Press)
- Stratagem Directions have been remapped to arrow keys (Up, Down, Left, Right)

## Contributing
### Adding a new Stratagem
- Add a new key to `assets/data/stratagems.json` with the key combination.
- Add icon with matching keyname.png to `assets/icons`.
- Add matching `actions.keyname.name` to `locales` files.
- Add matching `actions.keyname.labels.*` to `locales` files.

### Versioning

Here is the planned versioning convention...
[major release].[stratagem or feature add].[minor or bugfix]

major release = substantial change to the code base. For example, my icon rework that replaced every icon with vector graphics.

stratagem or feature add = AH adds a new stratagem that needs to be added.

minor or bugfix = clean up mistakes that occasionally slip through. 

## Attributions
### Icons
https://github.com/nvigneux/Helldivers-2-Stratagems-icons-svg
