LC_CTYPE=C && LANG=C && find . -type f | grep -v "\./\." | grep -i -v .jpg$ | grep -i -v .png$ | grep -i -v .pdf$ | grep -i -v .gif$ | grep -i -v .svg$ | grep -i -v .pyc$ | grep -i -v .eot$ | grep -i -v .ttf$ | grep -i -v .woff$ | grep -i -v .otf$ | grep -i -v .nc$ | grep -i -v .tif$ | grep -i -v "\./jquery_ui/" | grep -i -v "\./docs/" | grep -i -v .dbf$ | grep -i -v .prj$ | grep -i -v .shx$ | grep -i -v .cpg$ | grep -i -v .shp$ | grep -v "/tests/" | grep -v "/hs_docker_base/" | grep -v "/hydroshare/_xmlcache/" | grep -v "\./nginx/" | grep -v "\./hsctl" | grep -v "\./config/" | grep -v "\./irods/" | grep -v "\./run-pylint" | grep -v "\./run-test" | grep -v "\./Dockerfile" | grep -v "\./rebrand.sh" | grep -v "\./media_files/" | grep -v "\.git/" | grep -v "/log/" > grep.txt

LC_CTYPE=C && LANG=C && cat grep.txt | xargs grep -l "HydroShare" | xargs sed -i".sedbak" -e "s/HydroShare/CommonsShare/g"
LC_CTYPE=C && LANG=C && cat grep.txt | xargs grep -l "Hydroshare" | xargs sed -i".sedbak" -e "s/Hydroshare/CommonsShare/g"
