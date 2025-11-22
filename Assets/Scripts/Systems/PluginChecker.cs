using System.IO;
using UnityEditor;
using UnityEditor.PackageManager;
using UnityEngine;

namespace Systems
{
    [InitializeOnLoad]
    public class PluginChecker
    {
        static PluginChecker()
        {
            // Register callback for when packages are added, removed, or updated
            Events.registeredPackages += OnPackageChanged;
        }

        private static void OnPackageChanged(PackageRegistrationEventArgs args)
        {
            // Run the check whenever a package is changed
            CheckAndDefineSymbols();
            Debug.Log("changed");
        }

        private static void CheckAndDefineSymbols()
        {
            const string ovrPackageName = "com.meta.xr.sdk.core"; // The identifier of the OVR package
            bool ovrPluginExists = IsPackageInstalled(ovrPackageName);
            DefineSymbol("OVR_PLUGIN", ovrPluginExists);
        }

        private static bool IsPackageInstalled(string packageName)
        {
            string packagePath = Path.Combine("Library", "PackageCache");
            string[] packageFullPath = Directory.GetDirectories(packagePath, $"{packageName}@*");
            return packageFullPath.Length > 0;
        }

        private static void DefineSymbol(string symbol, bool shouldDefine)
        {
            BuildTargetGroup buildTargetGroup = EditorUserBuildSettings.selectedBuildTargetGroup;
            string symbols = PlayerSettings.GetScriptingDefineSymbolsForGroup(buildTargetGroup);

            bool containsSymbol = symbols.Contains(symbol);
            switch (shouldDefine)
            {
                case true when !containsSymbol:
                    symbols += (symbols.Length > 0 ? ";" : "") + symbol;
                    PlayerSettings.SetScriptingDefineSymbolsForGroup(buildTargetGroup, symbols);
                    break;
                case false when containsSymbol:
                    symbols = symbols.Replace(symbol + ";", "").Replace(symbol, "");
                    PlayerSettings.SetScriptingDefineSymbolsForGroup(buildTargetGroup, symbols);
                    break;
            }
        }
    }
}