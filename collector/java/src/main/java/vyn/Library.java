package vyn;

public class Library {

    private String name;

    private String version;

    private String author;

    private String description;

    public Library() {
    }

    public Library(String name,
                   String version,
                   String author,
                   String description) {

        this.name = name;
        this.version = version;
        this.author = author;
        this.description = description;

    }

}