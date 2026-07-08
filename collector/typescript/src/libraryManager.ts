export class LibraryManager {

    install(name: string): boolean {

        console.log(`Installing ${name}`);

        return true;

    }

    remove(name: string): boolean {

        console.log(`Removing ${name}`);

        return true;

    }

    update(name: string): boolean {

        console.log(`Updating ${name}`);

        return true;

    }

}