\# WristComp - Pip-Boy Style Smartwatch



A compact, retro-digital terminal application that simulates a wrist-worn survival device. Track your hydration, energy, stress, and manage your inventory in a persistent, keyboard-driven interface.



!\[Wrist Device Interface](https://via.placeholder.com/600x400?text=WristComp+Interface)



\## Features



\- \*\*Dashboard\*\*: Real-time clock, simulated battery, and all stats at a glance

\- \*\*Stats Management\*\*: Adjust hydration, energy, urination, and stress levels

\- \*\*Inventory\*\*: Add, use, and drop items with automatic stat effects

\- \*\*Persistent Storage\*\*: Everything saves to `watch\_data.json`

\- \*\*Keyboard Navigation\*\*: Full keyboard control with intuitive shortcuts



\## Installation



```bash

\# Create virtual environment

python3 -m venv venv

source venv/bin/activate  # On Windows: venv\\Scripts\\activate



\# Install dependencies

pip install textual

```



\## Usage



```bash

source venv/bin/activate

python wrist\_device.py

```



\### Navigation



| Key | Action |

|-----|--------|

| `1` | Go to Dashboard/Home |

| `2` | Go to Stats screen |

| `3` | Go to Inventory screen |

| `Esc` | Go back |

| `Q` | Quit (from dashboard) |



\### Inventory Actions



| Key | Action |

|-----|--------|

| `A` | Add new item |

| `U` | Use selected item |

| `D` | Drop selected item |



\### Consumable Items



| Item | Effect |

|------|--------|

| Water Flask | +25 Hydration, +10 Urination |

| Water | +15 Hydration, +10 Urination |

| Coffee | +15 Energy, +10 Urination |

| Energy Bar | +20 Energy |

| Medkit | -30 Stress |



\## Data Persistence



All data is stored in `watch\_data.json`:

\- Stats (hydration, energy, urination, stress)

\- Inventory with quantities

\- Device settings

\- Last updated timestamp



The app auto-saves on every change. You can reset stats or all data from the Settings screen.



\## File Structure



```

.

├── wrist\_device.py    # Main application with TUI screens

├── data\_store.py      # Data persistence layer

├── watch\_data.json    # Your saved data (auto-created)

└── venv/              # Virtual environment

```

