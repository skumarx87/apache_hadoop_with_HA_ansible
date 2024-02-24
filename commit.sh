cd /home/hadoop/apache_hadoop_with_HA_ansible

git config --global user.name "skumarx87"

git add *.yml
git add roles/*
git add vars/*
git add *.sh
git add commit.sh

git commit -am "initial commit"

git push origin
