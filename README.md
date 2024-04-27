# HELLDIVERS 2 StreamController Plugin
Assumes the following:
* Left Control will open Stratagem menu (Hold/Press)
* Stratagem Directions have been remapped to arrow keys (Up, Down, Left, Right)

## Contributing
### Adding a new Stratagem
* Add a new key to `assets/data/stratagems.json` with the key combination.
* Add icon with matching keyname.png to `assets/icons`.
* Add matching `actions.keyname.name` to `locales` files.

### TODO
* Better labels (add top/center/bottom instead of just name).
* Add "custom buttom" option where a user can define the stratagem itself.
* Package the icon set
* Test all the buttons
