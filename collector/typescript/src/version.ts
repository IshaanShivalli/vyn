export class Version {

    static newer(
        installed: string,
        latest: string
    ): boolean {

        return latest > installed;

    }

}