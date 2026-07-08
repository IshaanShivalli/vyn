#ifndef DEPENDENCY_MANAGER_H
#define DEPENDENCY_MANAGER_H

class DependencyManager
{
public:

    bool installDependencies();

    bool resolveDependencies();

    bool checkConflicts();
};

#endif