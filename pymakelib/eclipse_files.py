FILE_LANGUAJE_SETTING_XML = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<project>
        <configuration id="0.78511047.1277977235" name="pymaketool">
                <extension point="org.eclipse.cdt.core.LanguageSettingsProvider">
                        <provider copy-of="extension" id="org.eclipse.cdt.ui.UserLanguageSettingsProvider"/>
                        <provider-reference id="org.eclipse.cdt.core.ReferencedProjectsLanguageSettingsProvider" ref="shared-provider"/>
                        <provider-reference id="org.eclipse.cdt.managedbuilder.core.MBSLanguageSettingsProvider" ref="shared-provider"/>
						<!--wildcard_ls_provider-->
                </extension>
        </configuration>
</project>
"""

FILE_PROJECT = """<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
	<name>{0}</name>
	<comment></comment>
	<projects>
	</projects>
	<buildSpec>
		<buildCommand>
			<name>org.python.pydev.PyDevBuilder</name>
			<arguments>
			</arguments>
		</buildCommand>
		<buildCommand>
			<name>org.eclipse.cdt.managedbuilder.core.genmakebuilder</name>
			<triggers>clean,full,incremental,</triggers>
			<arguments>
			</arguments>
		</buildCommand>
		<buildCommand>
			<name>org.eclipse.cdt.managedbuilder.core.ScannerConfigBuilder</name>
			<triggers>full,incremental,</triggers>
			<arguments>
			</arguments>
		</buildCommand>
	</buildSpec>
	<natures>
		<nature>org.eclipse.cdt.core.cnature</nature>
		<nature>org.eclipse.cdt.core.ccnature</nature>
		<nature>org.eclipse.cdt.managedbuilder.core.managedBuildNature</nature>
		<nature>org.eclipse.cdt.managedbuilder.core.ScannerConfigNature</nature>
		<nature>org.python.pydev.pythonNature</nature>
	</natures>
</projectDescription>
"""

FILE_CPROJECT_TEMP = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<?fileVersion 4.0.0?><cproject storage_type_id="org.eclipse.cdt.core.XmlProjectDescriptionStorage">
	<storageModule moduleId="org.eclipse.cdt.core.settings">
		<cconfiguration id="0.78511047.1277977235">
			<storageModule buildSystemId="org.eclipse.cdt.managedbuilder.core.configurationDataProvider" id="0.78511047.1277977235" moduleId="org.eclipse.cdt.core.settings" name="pymaketool">
				<externalSettings/>
				<extensions>
					<extension id="org.eclipse.cdt.core.ELF" point="org.eclipse.cdt.core.BinaryParser"/>
					<extension id="org.eclipse.cdt.core.GASErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>
					<extension id="org.eclipse.cdt.core.GmakeErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>
					<extension id="org.eclipse.cdt.core.GLDErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>
					<extension id="org.eclipse.cdt.core.VCErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>
					<extension id="org.eclipse.cdt.core.CWDLocator" point="org.eclipse.cdt.core.ErrorParser"/>
					<extension id="org.eclipse.cdt.core.GCCErrorParser" point="org.eclipse.cdt.core.ErrorParser"/>
				</extensions>
			</storageModule>
			<storageModule moduleId="cdtBuildSystem" version="4.0.0">
				<configuration artifactName="${ProjName}" buildProperties="" description="" id="0.78511047.1277977235" name="pymaketool" optionalBuildProperties="org.eclipse.cdt.docker.launcher.containerbuild.property.volumes=,org.eclipse.cdt.docker.launcher.containerbuild.property.selectedvolumes=" parent="org.eclipse.cdt.build.core.prefbase.cfg">
					<folderInfo id="0.78511047.1277977235." name="/" resourcePath="">
						<toolChain id="org.eclipse.cdt.build.core.prefbase.toolchain.922644828" name="No ToolChain" resourceTypeBasedDiscovery="false" superClass="org.eclipse.cdt.build.core.prefbase.toolchain">
							<targetPlatform binaryParser="org.eclipse.cdt.core.ELF" id="org.eclipse.cdt.build.core.prefbase.toolchain.922644828.1436264033" name=""/>
							<builder id="org.eclipse.cdt.build.core.settings.default.builder.1098600423" keepEnvironmentInBuildfile="false" managedBuildOn="false" name="Gnu Make Builder" superClass="org.eclipse.cdt.build.core.settings.default.builder"/>
							<tool id="org.eclipse.cdt.build.core.settings.holder.libs.236666789" name="holder for library settings" superClass="org.eclipse.cdt.build.core.settings.holder.libs"/>
							<tool id="org.eclipse.cdt.build.core.settings.holder.1768859017" name="Assembly" superClass="org.eclipse.cdt.build.core.settings.holder">
								<inputType id="org.eclipse.cdt.build.core.settings.holder.inType.206126883" languageId="org.eclipse.cdt.core.assembly" languageName="Assembly" sourceContentType="org.eclipse.cdt.core.asmSource" superClass="org.eclipse.cdt.build.core.settings.holder.inType"/>
							</tool>
							<tool id="org.eclipse.cdt.build.core.settings.holder.1825177837" name="GNU C++" superClass="org.eclipse.cdt.build.core.settings.holder">
								<option IS_BUILTIN_EMPTY="false" IS_VALUE_EMPTY="false" id="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.compiler.include.paths.1447306494" name="Include paths (-I)" superClass="ilg.gnuarmeclipse.managedbuild.cross.option.cpp.compiler.include.paths" useByScannerDiscovery="true" valueType="includePath">
									
									<!--wildcard_c_includes-->

								</option>
								<inputType id="org.eclipse.cdt.build.core.settings.holder.inType.1720926587" languageId="org.eclipse.cdt.core.g++" languageName="GNU C++" sourceContentType="org.eclipse.cdt.core.cxxSource,org.eclipse.cdt.core.cxxHeader" superClass="org.eclipse.cdt.build.core.settings.holder.inType"/>
							</tool>
							<tool id="org.eclipse.cdt.build.core.settings.holder.1858450252" name="GNU C" superClass="org.eclipse.cdt.build.core.settings.holder">
								<option IS_BUILTIN_EMPTY="false" IS_VALUE_EMPTY="false" id="org.eclipse.cdt.build.core.settings.holder.incpaths.1905310811" superClass="org.eclipse.cdt.build.core.settings.holder.incpaths" valueType="includePath">
									<!--wildcard_c_includes-->
								</option>
								<option IS_BUILTIN_EMPTY="false" IS_VALUE_EMPTY="false" id="org.eclipse.cdt.build.core.settings.holder.symbols.1546279114" superClass="org.eclipse.cdt.build.core.settings.holder.symbols" valueType="definedSymbols">

									<!--wildcard_c_symbols-->

								</option>
								<inputType id="org.eclipse.cdt.build.core.settings.holder.inType.994335435" languageId="org.eclipse.cdt.core.gcc" languageName="GNU C" sourceContentType="org.eclipse.cdt.core.cSource,org.eclipse.cdt.core.cHeader" superClass="org.eclipse.cdt.build.core.settings.holder.inType"/>
							</tool>
						</toolChain>
					</folderInfo>
					<sourceEntries>
						<!--wildcard_c_exclude-->
					</sourceEntries>
				</configuration>
			</storageModule>
			<storageModule moduleId="org.eclipse.cdt.core.externalSettings"/>
		</cconfiguration>
	</storageModule>
	<storageModule moduleId="cdtBuildSystem" version="4.0.0">
		<project id="stm32h747disco.null.52182215" name="stm32h747disco"/>
	</storageModule>
	<storageModule moduleId="scannerConfiguration">
		<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		<scannerConfigBuildInfo instanceId="ilg.gnuarmeclipse.managedbuild.cross.toolchain.base.463944034;ilg.gnuarmeclipse.managedbuild.cross.toolchain.base.463944034.1798988395;ilg.gnuarmeclipse.managedbuild.cross.tool.c.compiler.2029807856;ilg.gnuarmeclipse.managedbuild.cross.tool.c.compiler.input.2042966102">
			<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		</scannerConfigBuildInfo>
		<scannerConfigBuildInfo instanceId="0.207144966">
			<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		</scannerConfigBuildInfo>
		<scannerConfigBuildInfo instanceId="0.711244623">
			<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		</scannerConfigBuildInfo>
		<scannerConfigBuildInfo instanceId="0.78511047.1277977235">
			<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		</scannerConfigBuildInfo>
		<scannerConfigBuildInfo instanceId="0.207144966;0.207144966.;com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler.304600552;com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.c.compiler.input.c.2021731310">
			<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		</scannerConfigBuildInfo>
		<scannerConfigBuildInfo instanceId="0.207144966;0.207144966.;com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.cpp.compiler.1511913342;com.st.stm32cube.ide.mcu.gnu.managedbuild.tool.cpp.compiler.input.cpp.1735336540">
			<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		</scannerConfigBuildInfo>
		<scannerConfigBuildInfo instanceId="ilg.gnuarmeclipse.managedbuild.cross.toolchain.base.463944034;ilg.gnuarmeclipse.managedbuild.cross.toolchain.base.463944034.1798988395;ilg.gnuarmeclipse.managedbuild.cross.tool.cpp.compiler.1603937698;ilg.gnuarmeclipse.managedbuild.cross.tool.cpp.compiler.input.2069329484">
			<autodiscovery enabled="true" problemReportingEnabled="true" selectedProfileId=""/>
		</scannerConfigBuildInfo>
	</storageModule>
	<storageModule moduleId="org.eclipse.cdt.core.LanguageSettingsProviders"/>
	<storageModule moduleId="refreshScope"/>
	<storageModule moduleId="org.eclipse.cdt.make.core.buildtargets"/>
</cproject>
"""
