#!/usr/bin/env python3
"""
Aplica o branding InfoDesk e configuracoes de servidor/discrição corporativa
sobre o codigo-fonte oficial do RustDesk (AGPL-3.0).
Falha imediatamente via AssertionError se qualquer trecho esperado não for encontrado.
"""

from pathlib import Path
import shutil
import sys


def replace_exact(path: Path, old: str, new: str, label: str) -> None:
    content = path.read_text(encoding="utf-8")
    assert old in content, f"[{label}] Trecho esperado nao encontrado em {path}"
    updated = content.replace(old, new, 1)
    assert new in updated, f"[{label}] Falha ao aplicar substituicao em {path}"
    path.write_text(updated, encoding="utf-8")
    print(f"OK [{label}] -> {path}")


def main() -> None:
    if len(sys.argv) != 3:
        print("Uso: apply_branding.py <rustdesk_dir> <assets_dir>", file=sys.stderr)
        sys.exit(2)

    rd = Path(sys.argv[1]).resolve()
    assets = Path(sys.argv[2]).resolve()

    assert rd.is_dir(), f"Diretorio RustDesk nao encontrado: {rd}"
    assert assets.is_dir(), f"Diretorio de assets nao encontrado: {assets}"

    # 1. libs/hbb_common/src/config.rs -> APP_NAME, RENDEZVOUS_SERVERS e RS_PUB_KEY
    hbb_config = rd / "libs" / "hbb_common" / "src" / "config.rs"
    replace_exact(
        hbb_config,
        'pub static ref APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
        'pub static ref APP_NAME: RwLock<String> = RwLock::new("InfoDesk".to_owned());',
        "hbb_common APP_NAME",
    )
    replace_exact(
        hbb_config,
        'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
        'pub const RENDEZVOUS_SERVERS: &[&str] = &["191.252.184.224"];',
        "hbb_common RENDEZVOUS_SERVERS",
    )
    replace_exact(
        hbb_config,
        'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
        'pub const RS_PUB_KEY: &str = "mNHyMm1XLFdd+5z+c16EtiT0isOEa89HcOa7FmuuDuA=";',
        "hbb_common RS_PUB_KEY",
    )

    # 2. src/tray.rs -> ocultar tray em modo silencioso e remover opcao "Stop service"
    tray_rs = rd / "src" / "tray.rs"
    replace_exact(
        tray_rs,
        'pub fn start_tray() {\n    if crate::ui_interface::get_builtin_option(hbb_common::config::keys::OPTION_HIDE_TRAY) == "Y" {',
        (
            "pub fn start_tray() {\n"
            "    if hbb_common::password_security::hide_cm() {\n"
            '        #[cfg(not(target_os = "macos"))]\n'
            "        {\n"
            "            return;\n"
            "        }\n"
            "    }\n"
            '    if crate::ui_interface::get_builtin_option(hbb_common::config::keys::OPTION_HIDE_TRAY) == "Y" {'
        ),
        "tray.rs start_tray hide_cm",
    )
    replace_exact(
        tray_rs,
        "tray_menu.append_items(&[&open_i, &quit_i]).ok();",
        "tray_menu.append_items(&[&open_i]).ok();",
        "tray.rs remove quit_i",
    )
    replace_exact(
        tray_rs,
        '            if crate::ui_interface::get_builtin_option(hbb_common::config::keys::OPTION_HIDE_TRAY) == "Y" {\n                return;\n            }',
        (
            "            if hbb_common::password_security::hide_cm()\n"
            '                || crate::ui_interface::get_builtin_option(hbb_common::config::keys::OPTION_HIDE_TRAY) == "Y"\n'
            "            {\n"
            "                return;\n"
            "            }"
        ),
        "tray.rs event_loop hide_cm",
    )

    # 3. src/core_main.rs -> --silent-install sem atalho no Desktop e sem Toast de instalacao
    core_main = rd / "src" / "core_main.rs"
    replace_exact(
        core_main,
        'let options = "desktopicon startmenu printer";',
        'let options = "startmenu printer";',
        "core_main.rs silent-install options",
    )
    replace_exact(
        core_main,
        (
            '            } else if args[0] == "--silent-install" {\n'
            '                if config::is_disable_installation() {\n'
            '                    return None;\n'
            '                }\n'
            '                #[cfg(not(windows))]\n'
            '                let options = "desktopicon startmenu";\n'
            '                #[cfg(windows)]\n'
            '                let options = "startmenu printer";\n'
            '                let res = platform::install_me(options, "".to_owned(), true, args.len() > 1);\n'
            '                let text = match res {\n'
            '                    Ok(_) => translate("Installation Successful!".to_string()),\n'
            '                    Err(err) => {\n'
            '                        println!("Failed with error: {err}");\n'
            '                        translate("Installation failed!".to_string())\n'
            '                    }\n'
            '                };\n'
            '                Toast::new(Toast::POWERSHELL_APP_ID)\n'
            '                    .title(&config::APP_NAME.read().unwrap())\n'
            '                    .text1(&text)\n'
            '                    .sound(Some(Sound::Default))\n'
            '                    .duration(Duration::Short)\n'
            '                    .show()\n'
            '                    .ok();\n'
            '                return None;'
        ),
        (
            '            } else if args[0] == "--silent-install" {\n'
            '                if config::is_disable_installation() {\n'
            '                    return None;\n'
            '                }\n'
            '                #[cfg(not(windows))]\n'
            '                let options = "startmenu";\n'
            '                #[cfg(windows)]\n'
            '                let options = "startmenu printer";\n'
            '                if let Err(err) = platform::install_me(options, "".to_owned(), true, args.len() > 1) {\n'
            '                    println!("Failed with error: {err}");\n'
            '                }\n'
            '                return None;'
        ),
        "core_main.rs suppress silent-install toast",
    )

    # 4. libs/portable/src/main.rs -> APP_PREFIX = "infodesk"
    portable_main = rd / "libs" / "portable" / "src" / "main.rs"
    replace_exact(
        portable_main,
        'const APP_PREFIX: &str = "rustdesk";',
        'const APP_PREFIX: &str = "infodesk";',
        "portable APP_PREFIX",
    )

    # 5. flutter/windows/runner/Runner.rc -> metadados InfoDesk
    runner_rc = rd / "flutter" / "windows" / "runner" / "Runner.rc"
    replace_exact(
        runner_rc,
        'VALUE "CompanyName", "Purslane Ltd" "\\0"',
        'VALUE "CompanyName", "InfoSistemas Solucoes em Tecnologia" "\\0"',
        "Runner.rc CompanyName",
    )
    replace_exact(
        runner_rc,
        'VALUE "FileDescription", "RustDesk Remote Desktop" "\\0"',
        'VALUE "FileDescription", "InfoDesk Remote Support" "\\0"',
        "Runner.rc FileDescription",
    )
    replace_exact(
        runner_rc,
        'VALUE "InternalName", "rustdesk" "\\0"',
        'VALUE "InternalName", "infodesk" "\\0"',
        "Runner.rc InternalName",
    )
    replace_exact(
        runner_rc,
        'VALUE "ProductName", "RustDesk" "\\0"',
        'VALUE "ProductName", "InfoDesk" "\\0"',
        "Runner.rc ProductName",
    )

    # 6. Substituicao de icones
    icon_targets = [
        (assets / "app_icon.ico", rd / "res" / "icon.ico"),
        (assets / "app_icon.ico", rd / "res" / "tray-icon.ico"),
        (assets / "app_icon.ico", rd / "flutter" / "windows" / "runner" / "resources" / "app_icon.ico"),
        (assets / "icon.png", rd / "res" / "icon.png"),
        (assets / "128x128@2x.png", rd / "res" / "128x128@2x.png"),
        (assets / "128x128.png", rd / "res" / "128x128.png"),
        (assets / "64x64.png", rd / "res" / "64x64.png"),
        (assets / "32x32.png", rd / "res" / "32x32.png"),
    ]
    for src, dst in icon_targets:
        assert src.is_file(), f"Asset ausente: {src}"
        assert dst.parent.is_dir(), f"Pasta destino ausente: {dst.parent}"
        shutil.copy2(src, dst)
        print(f"OK [icon] {src.name} -> {dst}")

    # 7. Supressao da janela flutuante --cm em sessoes headless autorizadas (Terminal / FileTransfer / PortForward)
    main_dart = rd / "flutter" / "lib" / "main.dart"
    replace_exact(
        main_dart,
        (
            '  final hide = await bind.cmGetConfig(name: "hide_cm") == \'true\';\n'
            '  gFFI.serverModel.hideCm = hide;\n'
            '  if (hide) {\n'
            '    await hideCmWindow(isStartup: true);\n'
            '  } else {\n'
            '    await showCmWindow(isStartup: true);\n'
            '  }'
        ),
        (
            '  final hide = await bind.cmGetConfig(name: "hide_cm") == \'true\';\n'
            '  gFFI.serverModel.hideCm = hide;\n'
            '  await hideCmWindow(isStartup: true);'
        ),
        "main.dart start cm hidden until non-headless session",
    )
    replace_exact(
        main_dart,
        (
            '  } else if (_isCmReadyToShow) {\n'
            '    if (await windowManager.getOpacity() != 1) {\n'
            '      await windowManager.setOpacity(1);'
        ),
        (
            '  } else if (_isCmReadyToShow) {\n'
            '    if (await windowManager.getOpacity() != 1) {\n'
            '      await windowManager.show();\n'
            '      await windowManager.setOpacity(1);'
        ),
        "main.dart showCmWindow unhide when visible session arrives",
    )

    server_model_dart = rd / "flutter" / "lib" / "models" / "server_model.dart"
    replace_exact(
        server_model_dart,
        "  bool hideCm = false;",
        (
            "  bool hideCm = false;\n\n"
            "  bool get shouldHideCmNow {\n"
            "    if (hideCm) return true;\n"
            "    final active = _clients.where((c) => !c.disconnected).toList();\n"
            "    if (active.isEmpty) return false;\n"
            "    return active.every((c) =>\n"
            "        c.authorized &&\n"
            "        (c.isFileTransfer || c.isTerminal || c.portForward.isNotEmpty) &&\n"
            "        !c.inVoiceCall &&\n"
            "        !c.incomingVoiceCall);\n"
            "  }"
        ),
        "server_model.dart shouldHideCmNow getter",
    )
    replace_exact(
        server_model_dart,
        (
            "          if (_clients.isEmpty) {\n"
            "            hideCmWindow();\n"
            "            if (_zeroClientLengthCounter++ == 12) {\n"
            "              // 6 second\n"
            "              windowManager.close();\n"
            "            }\n"
            "          } else {\n"
            "            _zeroClientLengthCounter = 0;\n"
            "            if (!hideCm) showCmWindow();\n"
            "          }"
        ),
        (
            "          if (_clients.isEmpty) {\n"
            "            hideCmWindow();\n"
            "            if (_zeroClientLengthCounter++ == 12) {\n"
            "              // 6 second\n"
            "              windowManager.close();\n"
            "            }\n"
            "          } else if (shouldHideCmNow) {\n"
            "            _zeroClientLengthCounter = 0;\n"
            "            hideCmWindow();\n"
            "          } else {\n"
            "            _zeroClientLengthCounter = 0;\n"
            "            showCmWindow();\n"
            "          }"
        ),
        "server_model.dart timerCallback headless cm hide",
    )
    replace_exact(
        server_model_dart,
        (
            "    if (desktopType == DesktopType.cm) {\n"
            "      if (_clients.isEmpty) {\n"
            "        hideCmWindow();\n"
            "      } else if (!hideCm) {\n"
            "        showCmWindow();\n"
            "      }\n"
            "    }"
        ),
        (
            "    if (desktopType == DesktopType.cm) {\n"
            "      if (_clients.isEmpty || shouldHideCmNow) {\n"
            "        hideCmWindow();\n"
            "      } else {\n"
            "        showCmWindow();\n"
            "      }\n"
            "    }"
        ),
        "server_model.dart updateClientState headless cm hide",
    )
    replace_exact(
        server_model_dart,
        (
            "      if (desktopType == DesktopType.cm && !hideCm) {\n"
            "        showCmWindow();\n"
            "      }"
        ),
        (
            "      if (desktopType == DesktopType.cm) {\n"
            "        if (shouldHideCmNow) {\n"
            "          hideCmWindow();\n"
            "        } else {\n"
            "          showCmWindow();\n"
            "        }\n"
            "      }"
        ),
        "server_model.dart addConnection headless cm hide",
    )
    replace_exact(
        server_model_dart,
        (
            "    Future.delayed(Duration.zero, () async {\n"
            "      if (!hideCm) windowOnTop(null);\n"
            "    });\n"
            "    // Only do the hidden task when on Desktop.\n"
            "    if (client.authorized && isDesktop) {\n"
            "      cmHiddenTimer = Timer(const Duration(seconds: 3), () {\n"
            "        if (!hideCm) windowManager.minimize();\n"
            "        cmHiddenTimer = null;\n"
            "      });\n"
            "    }"
        ),
        (
            "    Future.delayed(Duration.zero, () async {\n"
            "      if (!shouldHideCmNow) windowOnTop(null);\n"
            "    });\n"
            "    // Only do the hidden task when on Desktop.\n"
            "    if (client.authorized && isDesktop) {\n"
            "      cmHiddenTimer = Timer(const Duration(seconds: 3), () {\n"
            "        if (!shouldHideCmNow) windowManager.minimize();\n"
            "        cmHiddenTimer = null;\n"
            "      });\n"
            "    }"
        ),
        "server_model.dart _addTab headless cm hide",
    )

    print("Branding InfoDesk aplicado com sucesso.")


if __name__ == "__main__":
    main()
