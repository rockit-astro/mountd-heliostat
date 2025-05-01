Name:      rockit-mount-heliostat
Version:   %{_version}
Release:   1
Summary:   Heliostat control
Url:       https://github.com/rockit-astro/mountd-heliostat
License:   GPL-3.0
BuildArch: noarch

%description


%build
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}/etc/bash_completion.d
mkdir -p %{buildroot}%{_sysconfdir}/mountd/

%{__install} %{_sourcedir}/tel %{buildroot}%{_bindir}
%{__install} %{_sourcedir}/heliostat_mountd %{buildroot}%{_bindir}
%{__install} %{_sourcedir}/heliostat_mountd@.service %{buildroot}%{_unitdir}
%{__install} %{_sourcedir}/completion/tel %{buildroot}/etc/bash_completion.d

%{__install} %{_sourcedir}/heliostat.json %{buildroot}%{_sysconfdir}/mountd

%package server
Summary:  Heliostat control server.
Group:    Unspecified
Requires: python3-rockit-mount-heliostat
%description server

%files server
%defattr(0755,root,root,-)
%{_bindir}/heliostat_mountd
%defattr(0644,root,root,-)
%{_unitdir}/heliostat_mountd@.service

%package client
Summary:  Heliostat control client.
Group:    Unspecified
Requires: python3-rockit-mount-heliostat
%description client

%files client
%defattr(0755,root,root,-)
%{_bindir}/tel
/etc/bash_completion.d/tel

%package data-heliostat
Summary: Heliostat contorl configuration.
Group:   Unspecified
%description data-heliostat

%files data-heliostat
%defattr(0644,root,root,-)
%{_sysconfdir}/mountd/heliostat.json

%changelog
