RPMBUILD = rpmbuild --define "_topdir %(pwd)/build" \
        --define "_builddir %{_topdir}" \
        --define "_rpmdir %{_topdir}" \
        --define "_srcrpmdir %{_topdir}" \
        --define "_sourcedir %(pwd)"

all:
	mkdir -p build
	date --utc +%Y%m%d%H%M%S > VERSION
	${RPMBUILD} --define "_version %(cat VERSION)" -ba rockit-mount-heliostat.spec
	${RPMBUILD} --define "_version %(cat VERSION)" -ba python3-rockit-mount-heliostat.spec

	mv build/noarch/*.rpm .
	rm -rf build VERSION

install:
	@date --utc +%Y%m%d%H%M%S > VERSION
	@python3 -m build --outdir .
	@sudo pip3 install rockit.mount.heliostat-$$(cat VERSION)-py3-none-any.whl
	@rm VERSION
	@cp heliostat_mountd tel /bin/
	@cp heliostat_mountd@.service /usr/lib/systemd/system/
	@cp completion/tel /etc/bash_completion.d/
	@install -d /etc/mountd
	@echo ""
	@echo "Installed server, client, and service files."
	@echo "Now copy the relevant json config files to /etc/mountd/"
	@echo "and udev rules to /usr/lib/udev/rules.d/"