module.exports = {
  appId: 'org.institutionalsignals.desktop', productName: 'Institutional Signals',
  asar: true, directories: { output: 'release' },
  files: ['dist/**/*', 'desktop/*.cjs', '!desktop/test-*.cjs', 'package.json'],
  artifactName: 'Institutional-Signals-${version}-${os}-${arch}.${ext}',
  win: { target: ['nsis'] }, nsis: { oneClick: false, perMachine: false, allowToChangeInstallationDirectory: true },
  mac: { target: ['dmg', 'zip'], category: 'public.app-category.productivity', identity: null },
  linux: { target: ['AppImage', 'deb'], category: 'Office', maintainer: 'Institutional Signals' }
}
