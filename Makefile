p:
	git add .
	git commit -m '-'
	git push origin
	git push github_remote
push:
	make p
