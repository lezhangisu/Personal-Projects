//Credit goes to Ben Holland (ben-holland.com)
public class Quine {
	public static void main(String[] args) {
		char quote = 34;
		String code = "public class Quine { public static void main(String[] args) { char quote = 34; String code = ;System.out.print(code.substring(0,92) + quote + code + quote + code.substring(92, code.length())); } }";
		System.out.print(code.substring(0,92) + quote + code + quote + code.substring(92, code.length()));
	}
}
