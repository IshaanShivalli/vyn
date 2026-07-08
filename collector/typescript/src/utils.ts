export class Utils {

    static lower(text: string): string {

        return text.toLowerCase();

    }

    static startsWith(
        text: string,
        prefix: string
    ): boolean {

        return text.startsWith(prefix);

    }

}