# InfoDesk Custom Windows Client (AGPL-3.0)

Custom build automation for the **InfoDesk** Windows x64 remote support client based on upstream [RustDesk 1.4.6](https://github.com/rustdesk/rustdesk/releases/tag/1.4.6), distributed under **AGPL-3.0**.

## Customizations Applied at Build Time
- `APP_NAME = "InfoDesk"` (`InfoDesk.exe`, Windows service `InfoDesk`, `InfoDesk.toml` / `InfoDesk2.toml`)
- Built-in rendezvous server IP (`191.252.184.224`) and Ed25519 public key
- Native InfoSistemas branding icons (`assets/app_icon.ico`, PNG icons) and Windows version metadata
- Silent mode compliance when `allow-hide-cm = 'Y'` is configured in `InfoDesk2.toml` (no tray icon or Connection Manager popup)
- Disabled desktop shortcut and toast popup on `--silent-install`
