export class GitHub {

    rawURL(
        type: string,
        name: string,
        file: string
    ): string {

        return `https://raw.githubusercontent.com/IshaanShivalli/vyn-lib/main/${type}/${name}/${file}`;

    }

}