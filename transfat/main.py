#!/usr/bin/env python3
# coding: utf-8
"""Copy files to a device and fatsort that device.

Run this on the command line like so:

    $ transfat source1 source2 pathOnDrive

or do

    $ transfat -h

to see how to be fancier. Or read the README.md. Anyway, 2 things not
explained in either the help or the readme are as follows:

1. Armin mode:
    Armin mode is used to transfer episodes of the radio show "A State
    of Trance". It differs from non-Armin mode in that it has its own
    settings group in the config.ini, and that it calls a function that
    renames certain directory names on the root of the destination
    device.
2. Configuration setting PROMPT vs --non-interactive:
    In the config.ini file there are options to prompt for various
    actions; however you can also run the program with a
    --non-interactive flag. The two are mutually exclusive, and in such
    cases where they fight, the non-interactive flag always wins.
"""

from transfat import armin
from transfat import fatsort
from transfat import system
from transfat import talk
from transfat import transfer


def main():
    """The main script of transfat."""
    # Get runtime arguments
    args = system.getRuntimeArguments()

    # Read the configuration file
    talk.status("Reading config file '%s'" % args.config_file, args.verbose)

    cfgSettings = system.getConfigurationSettings(args.config_file,
                                                  args.default, args.armin,
                                                  args.quiet)
    if not cfgSettings:
        # Failure
        system.abort(1)
    else:
        # Success
        talk.success("'%s' read" % args.config_file, args.verbose)

    # Get root access if we don't have it already, and restart with it
    # if we don't. No need to do this if we're not fatsorting.
    if not args.no_fatsort:
        talk.status("Checking root access", args.verbose)

        rootAccess = system.requestRootAccess(cfgSettings,
                                              args.non_interactive,
                                              args.verbose)
        if not rootAccess:
            # Failed to run as root
            talk.error("Failed to run as root!", args.quiet)
            system.abort(1)
        else:
            # Success
            talk.success("Running as root", args.verbose)

    # Warn that this will take a bit of time if we're not fatsorting
    if not args.quiet:
        print("This may take a few minutes . . .")

    # Confirm that fatsort is installed
    if not args.no_fatsort:
        talk.status("Checking if fatsort is available", args.verbose)

        if fatsort.fatsortAvailable():
            # fatsort available
            talk.success("fatsort is available", args.verbose)
        else:
            # fatsort unavailable
            talk.error("fatsort not found!", args.quiet)
            system.abort(1)

    # Find device and mount location corresponding to provided
    # destination
    talk.status("Finding device and mount locations containing '%s'"
                % args.destination, args.verbose)

    # This function returns empty strings if it failed
    devLoc, mntLoc = fatsort.findDeviceLocations(args.destination,
                                                 args.non_interactive,
                                                 args.verbose,
                                                 args.quiet)
    if devLoc == '':
        # Failure
        talk.error("no FAT device found!", args.quiet)
        system.abort(1)
    else:
        # Success, print the devices
        if args.verbose:
            print("Success\n\nFound device and mount locations:"
                  "\ndevice: %s\nmount: %s" % (devLoc, mntLoc),
                  end='\n\n')

    # Get source and destination paths
    talk.status("Getting lists of source and destination paths",
                args.verbose)

    _, fromFiles, toDirs, toFiles = (
        transfer.getCorrespondingPathsLists(args.sources, args.destination,
                                            args.verbose, args.quiet))

    talk.success("Source and destination locations found", args.verbose)

    # Filter out certain file types based on settings in config file
    talk.status("Filtering out unwanted file types", args.verbose)

    transfer.filterOutExtensions(fromFiles, toFiles, cfgSettings,
                                 args.non_interactive)

    talk.success("Filtering complete", args.verbose)

    # Perform necessary audio file conversions
    talk.status("Starting to convert any audio files that need it",
                args.verbose)

    # Returns a list of temporary files to remove later
    tmpFiles = transfer.convertAudioFiles(fromFiles, toFiles, cfgSettings,
                                          args.non_interactive, args.verbose,
                                          args.quiet)

    talk.success("Conversions finished", args.verbose)

    # Create necessary directories to transfer to
    talk.status("Creating destination directories", args.verbose)

    transfer.createDirectories(toDirs, args.non_interactive, args.verbose,
                               args.quiet)

    talk.success("Destination directories created", args.verbose)

    # Copy source files to destination
    talk.status("Copying files", args.verbose)

    transfer.copyFiles(fromFiles, toFiles, cfgSettings, args.non_interactive,
                       args.verbose, args.quiet)

    talk.success("Files copied", args.verbose)

    # If in armin mode, rename destination directories
    if args.armin:
        talk.status("Renaming A State of Trance directories", args.verbose)

        armin.rename(mntLoc, args.quiet)

        talk.success("A State of Trance directories renamed", args.verbose)

    # Delete temporary files
    talk.status("Removing any temp files", args.verbose)

    transfer.deleteFiles(tmpFiles)

    talk.success("temp files removed", args.verbose)

    # Delete source directories if asked we're asked to. Note that
    # deleteSourceSetting - 1 is equivalent to a prompt flag, given the
    # config setting constant definitions.
    deleteSourceSetting = cfgSettings.getint("DeleteSources")
    promptFlag = deleteSourceSetting - 1

    if (deleteSourceSetting
       and not (args.non_interactive and promptFlag)):
        # Remove sources
        talk.status("Removing source files and directories", args.verbose)

        transfer.deletePaths(args.sources, promptFlag, args.verbose,
                             args.quiet)

        talk.success("source files and directories removed", args.verbose)

    # Unmount and fatsort if we're asked to
    if not args.no_fatsort:
        # Unmount
        talk.status("Unmounting %s" % mntLoc, args.verbose)

        if not fatsort.unmount(devLoc, args.verbose):
            talk.error("Failed to unmount %s!" % mntLoc, args.quiet)
            system.abort(1)
        else:
            talk.success("%s unmounted" % mntLoc, args.verbose)

        # Fatsort
        talk.status("fatsorting %s" % mntLoc, args.verbose)

        if not fatsort.fatsort(devLoc, args.verbose):
            talk.error("Failed to fatsort %s!" % mntLoc, args.quiet)
            system.abort(1)
        else:
            talk.success("%s fatsorted" % mntLoc, args.verbose)

    # Successful run
    talk.success("All done", args.verbose)

    return


if __name__ == '__main__':
    # This runs from the command line
    main()
