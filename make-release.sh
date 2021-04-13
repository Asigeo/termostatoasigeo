#!/bin/bash

# 1. Checked out into develop branch
git checkout develop
 
# 2. Fetched all remote updates
git remote update
 
# 3. Update local develop branch with remote copy
git pull origin develop
 
# 4. Created a release branch that tracks origin/develop
git checkout -b release/1.2 origin/develop
 
# 5. Pushed release branch to remote repository
git push origin release/1.2
 
# 6. Opened a "pull request" in GitHub for team to verify the release
 
# 7. Checkout into master branch
git checkout master
 
# 8. Updated local master branch with remote copy
git pull origin master
 
# 9. Merged release branch into master branch
git merge release/1.2
 
# 10. Tagged the release point by creating a new tag
git tag -a 1.2 -m 'Create release tag 1.2'
 
# 11. Pushed master branch to remote repository
git push origin master
 
# 12. Pushed the tags to remote repository
git push origin --tags
 
# 13. Checkout into develop branch
git checkout develop
 
# 14. Merged release branch into develop branch
git merge release/1.2
 
# 15. Pushed develop branch to remote repository
git push origin develop
 
# 16. Removed release branch from the local repository
git branch -D release/1.2
 
# 17. Removed release branch from the remote repository
git push origin :release/1.2