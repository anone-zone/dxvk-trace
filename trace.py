#!/bin/python

import argparse
import filecmp
import glob
import os
import pathlib
import shutil
import subprocess
import time

APITRACE_BINARIES = [
    "d3d8.dll",
    "d3d9.dll",
    "d3d10.dll",
    "d3d10_1.dll",
    "d3d11.dll",
    "dxgi.dll",
    "dxgitrace.dll",
]


def get_library_dirs():
    dirs = []

    vdf_path = os.path.expanduser("~/.steam/root/steamapps/libraryfolders.vdf")
    if not os.path.exists(vdf_path):
        raise FileNotFoundError(
            f"Could not find Steam library vdf: '{vdf_path}'")

    print(f"Reading libraries from '{vdf_path}'")
    vdf = open(vdf_path, "r")
    vdf_lines = vdf.readlines()

    for line in vdf_lines:
        if '"path"' in line:
            dir = line.split('"')[-2]
            dir = os.path.join(dir)
            if os.path.exists(dir):
                dirs.append(dir)

    if len(dirs) == 0:
        raise FileNotFoundError(
            f"Could not find Steam library directories in '{vdf_path}'")

    print(f"Found libraries: '{dirs}'")
    return dirs


def get_game_dir(appid):
    libraries = get_library_dirs()
    acf_name = f"appmanifest_{appid}.acf"

    for lib_path in libraries:
        acf_path = os.path.join(lib_path, "steamapps", acf_name)
        if os.path.exists(acf_path):
            break

    if not os.path.exists(acf_path):
        raise FileNotFoundError(
            f"Could not find Steam appmanifest: '{acf_name}'")

    print(f"Reading installdir from '{acf_path}'")
    acf = open(acf_path, "r")
    acf_lines = acf.readlines()

    game_dir = None
    for line in acf_lines:
        if '"installdir"' in line:
            game_dir = line.split('"')[-2]
            break

    if game_dir is None:
        raise FileNotFoundError(f"Could not find installdir in '{acf_path}'")

    full_game_path = None

    for lib_path in libraries:
        full_path = os.path.join(lib_path, "steamapps", "common", game_dir)
        if os.path.exists(full_path):
            full_game_path = full_path
            break

    if full_game_path is None:
        raise FileNotFoundError(
            f"Could not find game '{game_dir}' in libraries {libraries}")

    print(f"Found game path: '{full_game_path}'")
    return full_game_path


def get_game_compat_dir(appid):
    print("Getting compatdata path")
    libraries = get_library_dirs()
    for lib_path in libraries:
        compatdata_path = os.path.join(
            lib_path, "steamapps", "compatdata", appid)
        if os.path.exists(compatdata_path):
            break
    if not os.path.exists(compatdata_path):
        raise FileNotFoundError(
            f"Could not find compatdata for '{appid}' in libraries: '{libraries}'")
    return compatdata_path


def get_wine_desktop_dir(appid):
    game_compat_path = get_game_compat_dir(appid)
    desktop_path = os.path.join(
        game_compat_path, "pfx", "drive_c", "users", "steamuser", "Desktop")
    if not os.path.exists(desktop_path):
        raise FileNotFoundError(
            f"Could not find wine desktop: '{desktop_path}'")
    return desktop_path


def get_apitrace_install_dir(appid, rel_path):
    game_dir = get_game_dir(appid)

    if rel_path is not None:
        return os.path.join(game_dir, rel_path)

    return game_dir


def get_apitrace_source_dir(is_32_bit):
    if is_32_bit:
        path = os.path.abspath("apitrace-win32")
    else:
        path = os.path.abspath("apitrace-win64")
    dir = os.path.join(path, "lib", "wrappers")
    return dir


def is_apitrace_binary(path):
    source_32 = get_apitrace_source_dir(True)
    source_64 = get_apitrace_source_dir(False)

    for bin in APITRACE_BINARIES:
        bin_32 = os.path.join(source_32, bin)
        bin_64 = os.path.join(source_64, bin)
        if filecmp.cmp(path, bin_32):
            return True
        if filecmp.cmp(path, bin_64):
            return True

    return False


def uninstall_apitrace(appid, rel_path):
    print("Uninstalling apitrace...")
    install_dir = get_apitrace_install_dir(appid, rel_path)
    print(f"apitrace install dir: '{install_dir}'")

    for bin in APITRACE_BINARIES:
        install_path = os.path.join(install_dir, bin)

        if os.path.exists(install_path):
            if is_apitrace_binary(install_path):
                print(f"Removing apitrace binary: '{install_path}'")
                pathlib.Path.unlink(install_path)


def install_apitrace(appid, is_32_bit, rel_path):
    print("Installing apitrace...")
    source_dir = get_apitrace_source_dir(is_32_bit)
    print(f"apitrace source dir: '{source_dir}'")
    install_dir = get_apitrace_install_dir(appid, rel_path)
    print(f"apitrace install dir: '{install_dir}'")

    for bin in APITRACE_BINARIES:
        source_path = os.path.join(source_dir, bin)
        dest_path = os.path.join(install_dir, bin)

        if os.path.exists(dest_path):
            if is_apitrace_binary(dest_path):
                print(f"Removing existing apitrace binary: '{dest_path}'")
                pathlib.Path.unlink(dest_path)
            else:
                raise FileExistsError(
                    f"File already exists and is not apitrace: '{dest_path}'")

        print(f"Copying apitrace binary: '{source_path}' -> '{dest_path}'")
        shutil.copy(source_path, dest_path)


def get_vk_layer_path(is_32_bit):
    layer_path = os.path.abspath("gfxreconstruct")
    if is_32_bit:
        layer_path = os.path.join(layer_path, "build-32")
    else:
        layer_path = os.path.join(layer_path, "build-64")
    layer_path = os.path.join(layer_path, "layer")
    if not os.path.exists(layer_path):
        raise FileNotFoundError(
            f"Could not find gfxrecon layer: '{layer_path}'")
    return layer_path


def set_env_var(name, val):
    if val is None:
        print(f"rm env {name}")
        del os.environ[name]
    else:
        print(f"env {name}={val}")
        os.environ[name] = val


def set_env_vars(is_32_bit):
    print("Setting env variables")
    set_env_var("WINEDLLOVERRIDES", ",".join(APITRACE_BINARIES) + "=n,b")
    set_env_var("VK_LAYER_PATH", get_vk_layer_path(is_32_bit))
    set_env_var("VK_INSTANCE_LAYERS", "VK_LAYER_LUNARG_gfxreconstruct")


def launch_game(appid):
    print(f"Launching appid {appid}...")
    subprocess.Popen(["steam", "-applaunch", appid], env=os.environ)
    # HACK: apparently steam starts a steam.exe on launch for a brief time...?
    # this messes with wait_for_game_launch() / wait_for_game_exit()
    time.sleep(15)


def is_process_running(name):
    proc_list = os.popen("ps -Af").read()
    return proc_list.count(name) > 0


def wait_for_game_launch():
    # TODO: probably a better way to detect this?
    print("Waiting for game...")
    while not is_process_running("steam.exe"):
        time.sleep(1)


def wait_for_game_exit():
    print("Waiting for steam.exe to exit...")
    while is_process_running("steam.exe"):
        time.sleep(1)


# Needed for env vars...
# TODO: Could grab proton version from compatdata
# and create user_settings.py...
def kill_steam():
    os.popen("killall steam")
    time.sleep(5)


def move_trace_files(appid):
    print("Moving trace files")

    game_path = get_game_dir(appid)
    desktop_path = get_wine_desktop_dir(appid)
    vk_traces = glob.glob("*.gfxr", root_dir=game_path, recursive=False)
    d3d_traces = glob.glob("*.trace", root_dir=desktop_path, recursive=False)

    target_dir = os.path.abspath("traces")
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    for tr in vk_traces:
        tr = os.path.join(game_path, tr)
        target_path = os.path.join(target_dir, os.path.basename(tr))
        print(f"moving '{tr}' -> '{target_path}'")
        shutil.move(tr, target_path)

    for tr in d3d_traces:
        tr = os.path.join(desktop_path, tr)
        basename = os.path.basename(tr)
        target_path = os.path.join(target_dir, basename)
        print(f"Moving '{tr}' -> '{target_path}'")
        shutil.move(tr, target_path)

        comp_name = basename.split(".trace")[0] + "-compressed.trace"
        comp_path = os.path.join(target_dir, comp_name)
        print(f"Compressing '{target_path}' -> {comp_path}")
        subprocess.run(
            ["apitrace", "repack", "--brotli=2", target_path, comp_path])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--x86', action='store_true',
                        help="Use for 32-bit games.")
    parser.add_argument('-u', '--uninstall', action='store_true',
                        help="Uninstall existing apitrace binaries from the game directory.")
    parser.add_argument('-i', '--install_dir',
                        help="Relative path to game root to install apitrace to.")
    parser.add_argument('appid', help="The appid to launch on Steam.")
    args = parser.parse_args()

    if args.uninstall:
        uninstall_apitrace(args.appid, args.install_dir)
        exit()

    install_apitrace(args.appid, args.x86, args.install_dir)
    kill_steam()
    set_env_vars(args.x86)
    launch_game(args.appid)
    wait_for_game_launch()
    wait_for_game_exit()
    kill_steam()
    uninstall_apitrace(args.appid, args.install_dir)
    move_trace_files(args.appid)
